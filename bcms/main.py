"""Main module"""

import asyncio
import getpass
import time
import socket
import logging
from bleak.backends.device import BLEDevice
from bleak import BleakScanner
from px_python_shared import send_alert
from bcms.api import BackendAPI
from bcms.data_store import limit_iot_data_sample_rate
from . import log as _log
from .cli import parse_cli_params
from .config import (
    RPC_ADDRESS,
    RPC_PORT,
    SUPPORTED_DEVICES,
    BLUETOOTH_SCAN_INTERVAL,
    CLEAR_IOT_DATA_CACHE_INTERVAL,
    DATA_SUBMISSION_INTERVAL,
)
from .devices_classes import BCMSDeviceInfo
from .data_types import (
    DataType,
)
from .data_store import dump_iot_data_for_api_submission
from .ble_utils import process_supported_device, iot_advertisement_data_callback_wrapper
from .rpc_server import new_rpc_connection
from .bootstrap import (
    devices_mem,
    devices_data,
    async_queue,
    pair_device,
    unpair_device,
)


log = logging.getLogger(__name__)

class BCMS:
    backend_api = BackendAPI()
    use_device_identity = False
    application_identifier = None
    notify = False
    username = None
    sleep = BLUETOOTH_SCAN_INTERVAL
    sleep_data = DATA_SUBMISSION_INTERVAL

    def __init__(
        self,
        use_device_identity=False,
        application_identifier=None,
        notify=False,
        username=None,
        sleep=BLUETOOTH_SCAN_INTERVAL,
        sleep_data=DATA_SUBMISSION_INTERVAL,
    ):
        self.use_device_identity = use_device_identity
        self.application_identifier = application_identifier
        self.notify = notify
        self.username = username
        self.sleep = sleep
        self.sleep_data = sleep_data
        
        if self.use_device_identity:
            try:
                self.backend_api = BackendAPI()
                self.backend_api.load(application_identifier)
            except Exception as err:
                log.error("Failed to load backend api. Is this device registered?: %s", err)
                exit(1)
                
    async def start(self):
        def notify_callback(title: str, message: str, timeout: int = 5000):
            if self.notify:
                send_alert(self.username, title, message, timeout)

        await asyncio.gather(
            self.device_discovery_loop(notify_callback, self.sleep),
            self.cache_clear_old_data_loop(),
            self.rpc_server_loop(),
            self.api_data_submission_loop(self.sleep_data),
            self.register_devices_loop(),
        )
    

    async def device_discovery_loop(
        self, notify_callback, scan_interval: int
    ):
        """Discover devices and store BLE data"""

        def store_data(data: DataType):
            """If device exists in memory, store data"""
            if devices_mem.exists(data.address):
                devices_data.add(data)

        def track_device(device: BLEDevice):
            """If device is known, update last seen time, otherwise add it to memory"""
            exists_mem = devices_mem.get(device.address)
            if exists_mem is not None and exists_mem.name is not device.name:
                # Update device name if it has changed
                devices_mem.replace(
                    BCMSDeviceInfo(
                        address=device.address,
                        name=device.name,
                        approved=exists_mem.approved,
                        paired=exists_mem.paired,
                        id=exists_mem.id,
                        is_registered=exists_mem.is_registered,
                    )
                )
            elif exists_mem is not None:
                # Update last seen time if device is already known
                devices_mem.update_last_seen(device.address)
            else:
                devices_mem.add(
                    BCMSDeviceInfo(
                        address=device.address,
                        name=device.name,
                        approved=False,
                        paired=False,
                    )
                )

        async def connect_device(device: BLEDevice):
            """Connect to device to update time and retrieve data"""
            for supported in SUPPORTED_DEVICES:
                if device.name.startswith(supported):
                    log.debug("=> Connecting to %s", device)
                    notify_callback("Connecting", f"Connecting to {device.name}", 10000)
                    try:
                        await process_supported_device(
                            device,
                            notify_callback=notify_callback,
                            store_data_callback=store_data,
                        )
                    except Exception as err:
                        log.error("Failed with error on %s: %s", device.name, err)
                        if notify_callback:
                            notify_callback(
                                "Error", f"Failed with error on {device.name}: {err}", 10000
                            )
                    break

        while True:
            scanner = BleakScanner(
                detection_callback=iot_advertisement_data_callback_wrapper(
                    store_data_callback=store_data, track_device_callback=track_device
                )
            )

            log.debug("=> Starting BLE scan")
            await scanner.start()
            await asyncio.sleep(scan_interval)
            await scanner.stop()

            discovered = scanner.discovered_devices

            # Connect to devices
            for device in discovered:
                in_memory = devices_mem.get(device.address)
                if in_memory and in_memory.paired is True:
                    await connect_device(device)

            await asyncio.sleep(1)
            await self.process_async_queue(notify_callback=notify_callback)


    async def rpc_server_loop(self):
        """Start RPC server"""
        server = await asyncio.start_server(
            new_rpc_connection, RPC_ADDRESS, RPC_PORT, family=socket.AF_INET
        )
        async with server:
            await server.serve_forever()


    async def cache_clear_old_data_loop(
        self, interval=CLEAR_IOT_DATA_CACHE_INTERVAL, max_age=CLEAR_IOT_DATA_CACHE_INTERVAL
    ):
        """Clear old data every 60 seconds"""
        while True:
            log.debug("=> Clearing old data")
            devices_data.clear_old_data(max_age)
            await asyncio.sleep(interval)


    async def api_data_submission_loop(
        self, data_submission_interval: int
    ):
        """Submit data to API every 10 seconds"""
        last_submission = None
        while True:
            registered_devices = devices_mem.get_registered()

            # Backend not loaded; Cannot submit data
            if not self.backend_api.is_loaded:
                log.info("=> [DEMO] No backend API loaded")

                from_time = None
                if last_submission and isinstance(last_submission, int):
                    from_time = last_submission
                else:
                    from_time = round(time.time() - 60)
                to_time = round(time.time())
                log.debug("=> Fetching data from %s to %s", from_time, to_time)
                data = devices_data.get(from_time=from_time, to_time=to_time)
                log.debug("   Found %s entries", len(data))
                sample_data = limit_iot_data_sample_rate(data)
                log.debug("   Found %s entries - SAMPLED", len(sample_data))
                formatted_data = dump_iot_data_for_api_submission(
                    sample_data, registered_devices
                )
                if len(sample_data) > 0:
                    log.debug("=> [DEMO] Submitting %s entries to API", len(sample_data))
                else:
                    log.debug("=> [DEMO] Submitting entries to API: Nothing to submit")
                last_submission = to_time

                await asyncio.sleep(data_submission_interval)
                continue

            # Backend API loaded; Submit data
            if last_submission is None:
                last_submissions = []

                # If we haven't submitted before, determine last timestamp
                known_devices = devices_mem.get_all()
                for device in known_devices:
                    if device.approved is True:
                        if device.id is None:
                            continue

                        last_data_timestamp = await self.backend_api.last_iot_device_data_submission(
                            device.id
                        )
                        last_submissions.append(
                            {"address": device.address, "last_submission": last_data_timestamp}
                        )
                        log.debug("   Last submission for %s: %s", device, last_data_timestamp)

                filtered_data = []
                to_time = round(time.time())

                for device in last_submissions:
                    log.debug(
                        "=> Fetching data for %s, from %s to %s",
                        device,
                        device["last_submission"],
                        to_time,
                    )
                    from_time = device["last_submission"]
                    data = devices_data.get(
                        from_time=from_time,
                        to_time=to_time,
                        device_address=device["address"],
                    )
                    log.debug("   Found %s entries", len(data))
                    filtered_data.extend(data)

                sample_data = limit_iot_data_sample_rate(filtered_data)
                log.debug("   Found %s entries - SAMPLED", len(sample_data))
                formatted_data = dump_iot_data_for_api_submission(
                    sample_data, registered_devices
                )
                if len(sample_data) > 0:
                    log.debug("=> Submitting %s entries to API", len(sample_data))
                    await self.backend_api.submit_iot_data(formatted_data)
                else:
                    log.debug("=> Submitting entries to API: Nothing to submit")

                last_submission = to_time

            else:
                # If we know the last submission, only submit data since then
                to_time = round(time.time())
                log.debug("=> Fetching data from %s to %s", last_submission, to_time)
                data = devices_data.get(from_time=last_submission, to_time=to_time)
                log.debug("   Found %s entries", len(data))
                sample_data = limit_iot_data_sample_rate(data)
                log.debug("   Found %s entries - SAMPLED", len(sample_data))
                formatted_data = dump_iot_data_for_api_submission(
                    sample_data, registered_devices
                )
                if len(sample_data) > 0:
                    log.debug("=> Submitting %s entries to API", len(sample_data))
                    await self.backend_api.submit_iot_data(formatted_data)
                else:
                    log.debug("=> Submitting entries to API: Nothing to submit")

                last_submission = to_time

            await asyncio.sleep(data_submission_interval)


    async def process_async_queue(self, notify_callback=None):
        """Process async queue"""

        def pairing_success_callback(address: str, name: str = None):
            log.debug("Pair success %s", address)
            if self.backend_api.is_loaded:
                try:
                    result = self.backend_api.create_iot_device_if_not_exists(address)
                    if result and result.id:
                        devices_mem.replace(
                            BCMSDeviceInfo(
                                address=address,
                                name=name,
                                approved=True,
                                paired=True,
                                id=result.id,
                                is_registered=True,
                            )
                        )
                except Exception as err:
                    log.error("Failed to create iot device %s: %s", address, err)

        if len(async_queue) > 0:
            item = async_queue.get()
            if item.command == "pair":
                log.info("Pairing %s", item.args["address"])
                try:
                    await pair_device(
                        item.args["address"], pairing_success_callback, notify_callback
                    )
                except Exception as err:
                    log.error("Unknown pair err: %s", err)
            elif item.command == "unpair":
                log.info("Unpairing %s", item.args["address"])
                try:
                    await unpair_device(item.args["address"], notify_callback)
                except Exception as err:
                    log.error("Unknown unpair err: %s", err)


    async def register_devices_loop(self):
        while True:
            log.debug("=> Registering devices")
            if self.backend_api.is_loaded:
                devices = devices_mem.get_approved_or_paired()

                # sleep 2s, in case the device was just added, and another registration is ongoing
                # better approach: add created_at and use that to "delay"
                await asyncio.sleep(2)

                for device in devices:
                    is_current = device.last_checked_seconds_ago(60 * 60)  # 1 hour
                    if is_current or device.is_registered is False:
                        log.debug("Checking if device is registered: %s", device.address)
                    else:
                        log.debug(
                            "Skipping device %s, last checked %s",
                            device.address,
                            device.last_checked_timestamp,
                        )
                        continue

                    try:
                        result = self.backend_api.create_iot_device_if_not_exists(device.address)
                        log.debug("Result: %s", result)

                        if (
                            result
                            and result.exists
                            and result.remember_device is True
                            and result.id
                        ):
                            if result.id == device.id and device.is_registered is True:
                                # device is already registered
                                continue
                            devices_mem.replace(
                                BCMSDeviceInfo(
                                    address=device.address,
                                    name=device.name,
                                    approved=True,
                                    paired=device.paired,
                                    id=result.id,
                                    is_registered=True,
                                )
                            )
                        else:
                            # device is not registered
                            devices_mem.replace(
                                BCMSDeviceInfo(
                                    address=device.address,
                                    name=device.name,
                                    approved=True,
                                    paired=device.paired,
                                    id=None,
                                    is_registered=False,
                                )
                            )
                    except Exception as err:
                        log.error(
                            "Failed to check / register device %s: %s", device.address, err
                        )

            await asyncio.sleep(60)

def main():
    params = parse_cli_params()
    username = params["username"]
    notify = params["notify"]
    sleep = params["sleep"]
    sleep_data = params["sleep_data"]
    use_device_identity = params["use_device_identity"]
    application_identifier = params["application_identifier"]
    debug = params["debug"]

    if getpass.getuser() != "root":
        _log.set_nonroot_logging()

    if debug:
        _log.set_debugging(log)
        
    bcms = BCMS(
        use_device_identity=use_device_identity,
        application_identifier=application_identifier,
        notify=notify,
        username=username,
        sleep=sleep,
        sleep_data=sleep_data,
    )

    asyncio.run(
        bcms.start()
    )


if __name__ == "__main__":
    main()
