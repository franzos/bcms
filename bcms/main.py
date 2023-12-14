import asyncio
import time
import socket
import logging
from bleak.backends.device import BLEDevice
from bleak import BleakScanner
from vhh_bluetooth_terminal_assigned_user import send_alert

from bcms.data_store import limit_iot_data_sample_rate

from .log import *
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
    backend_api,
    async_queue,
    pair_device,
    unpair_device,
)


log = logging.getLogger(__name__)


async def device_discovery_loop(notify_callback=None):
    """Discover devices and store BLE data"""

    def store_data(data: DataType):
        if devices_mem.exists(data.address):
            devices_data.add(data)

    def track_device(device: BLEDevice):
        exists_mem = devices_mem.get(device.address)
        if exists_mem is not None and exists_mem.name is not device.name:
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
                log.info("=> Connecting to %s", device)
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
        await asyncio.sleep(BLUETOOTH_SCAN_INTERVAL)
        await scanner.stop()

        discovered = scanner.discovered_devices

        # Connect to devices
        for device in discovered:
            in_memory = devices_mem.get(device.address)
            if in_memory and in_memory.paired is True:
                await connect_device(device)

        await asyncio.sleep(1)
        await process_async_queue(notify_callback=notify_callback)


async def rpc_server_loop():
    """Start RPC server"""
    server = await asyncio.start_server(
        new_rpc_connection, RPC_ADDRESS, RPC_PORT, family=socket.AF_INET
    )
    async with server:
        await server.serve_forever()


async def cache_clear_old_data_loop(
    interval=CLEAR_IOT_DATA_CACHE_INTERVAL, max_age=CLEAR_IOT_DATA_CACHE_INTERVAL
):
    """Clear old data every 60 seconds"""
    while True:
        log.debug("=> Clearing old data")
        devices_data.clear_old_data(max_age)
        await asyncio.sleep(interval)


async def api_data_submission_loop():
    """Submit data to API every 10 seconds"""
    last_submission = None
    while True:
        registered_devices = devices_mem.get_registered()
        if backend_api and backend_api.is_loaded:
            if last_submission is None:
                last_submissions = []

                # If we haven't submitted before, determine last timestamp
                known_devices = devices_mem.get_all()
                for device in known_devices:
                    if device.approved is True:
                        if device.id is None:
                            continue

                        last_data = await backend_api.last_iot_device_data_submission(
                            device.id
                        )
                        last_submissions.append(
                            {"address": device.address, "last_submission": last_data}
                        )
                        log.debug("   Last submission for %s: %s", device, last_data)

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
                log.info("=> Submitting %s entries to API", len(sample_data))
                await backend_api.submit_iot_data(formatted_data)

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
                log.info("=> Submitting %s entries to API", len(sample_data))
                await backend_api.submit_iot_data(formatted_data)

                last_submission = to_time
        else:
            from_time = None
            if last_submission:
                from_time = last_submission
            else:
                from_time = round(time.time() - 60)
            to_time = round(time.time())
            log.info("=> Fetching data from %s to %s", from_time, to_time)
            data = devices_data.get(from_time=from_time, to_time=to_time)
            log.debug("   Found %s entries", len(data))
            sample_data = limit_iot_data_sample_rate(data)
            log.debug("   Found %s entries - SAMPLED", len(sample_data))
            formatted_data = dump_iot_data_for_api_submission(
                sample_data, registered_devices
            )
            log.info("=> [DEMO] Submitting %s entries to API", len(sample_data))
            last_submission = to_time

        await asyncio.sleep(DATA_SUBMISSION_INTERVAL)


async def process_async_queue(notify_callback=None):
    """Process async queue"""

    def pairing_success_callback(address: str, name: str = None):
        log.debug("Pair success %s", address)
        if backend_api.is_loaded:
            try:
                result = backend_api.create_iot_device_if_not_exists(address)
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
            except Exception as e:
                log.error("Failed to create iot device %s: %s", address, e)

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


async def register_devices_loop():
    while True:
        log.debug("=> Registering devices")
        if backend_api.is_loaded:
            devices = devices_mem.get_approved_or_paired()

            # sleep 2s, in case the device was just added, and another registration is ongoing
            # better approach: add created_at and use that to "delay"
            await asyncio.sleep(2)
            for device in devices:
                log.debug("Checking if device is registered: %s", device.address)
                try:
                    result = backend_api.create_iot_device_if_not_exists(device.address)
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
                except Exception as e:
                    log.error(
                        "Failed to check / register device %s: %s", device.address, e
                    )

        await asyncio.sleep(60)


async def process(
    use_device_identity=False,
    application_identifier=None,
    username=None,
):
    if use_device_identity:
        try:
            backend_api.load(application_identifier)
        except Exception as e:
            log.error("Failed to load backend api. Is this device registered?: %s", e)
            exit(1)

    def notify_callback(title: str, message: str, timeout: int = 5000):
        log.debug("Notify callback")
        send_alert(username, title, message, timeout)

    await asyncio.gather(
        device_discovery_loop(notify_callback=notify_callback),
        cache_clear_old_data_loop(),
        rpc_server_loop(),
        api_data_submission_loop(),
        register_devices_loop(),
    )


# if __name__ == "__main__":


def main():
    params = parse_cli_params()
    debug = params["debug"]
    username = "username" in params and params["username"] or None
    use_device_identity = (
        "use_device_identity" in params and params["use_device_identity"] or False
    )
    application_identifier = (
        "application_identifier" in params and params["application_identifier"] or None
    )

    if debug:
        ch.setLevel(logging.DEBUG)

    asyncio.run(
        process(
            use_device_identity=use_device_identity,
            application_identifier=application_identifier,
            username=username,
        )
    )
