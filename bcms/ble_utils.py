import logging
import time
import asyncio
import struct
from datetime import datetime, timedelta
from bleak import BleakClient, BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from typing import List

from .data_types import (
    BloodPressureData,
    DataType,
    TemperatureData,
    BatteryLevelData,
    AdvertisementData,
    HeartRateData,
    PressureData,
    AlertData,
)


log = logging.getLogger(__name__)


def _read_sfloat_le(buffer, index):
    data = struct.unpack_from("<H", buffer, index)[0]
    mantissa = data & 0x0FFF
    if (mantissa & 0x0800) > 0:
        mantissa = -1 * (~(mantissa - 0x01) & 0x0FFF)
    exponential = data >> 12
    return mantissa * pow(10, exponential)


def decode_data(data, battery):
    """Decode data from device"""
    buf = bytearray(data)
    flags = buf[0]
    result = {}
    index = 1

    if flags & 0x01:
        result["SystolicPressure_kPa"] = _read_sfloat_le(buf, index)
        index += 2
        result["DiastolicPressure_kPa"] = _read_sfloat_le(buf, index)
        index += 2
        result["MeanArterialPressure_kPa"] = _read_sfloat_le(buf, index)
        index += 2
    else:
        result["SystolicPressure_mmHg"] = _read_sfloat_le(buf, index)
        index += 2
        result["DiastolicPressure_mmHg"] = _read_sfloat_le(buf, index)
        index += 2
        result["MeanArterialPressure_mmHg"] = _read_sfloat_le(buf, index)
        index += 2

    if flags & 0x02:
        result["date"] = {
            "year": struct.unpack("<H", buf[index : index + 2])[0],
            "month": buf[index + 2],
            "day": buf[index + 3],
            "hour": buf[index + 4],
            "minute": buf[index + 5],
            "second": buf[index + 6],
        }
        index += 7

    if flags & 0x04:
        result["PulseRate"] = _read_sfloat_le(buf, index)
        index += 2

    if flags & 0x08:
        index += 1

    if flags & 0x10:
        ms = buf[index]
        result["bodyMoved"] = (ms & 0b1) != 0
        result["cuffFitLoose"] = (ms & 0b10) != 0
        result["irregularPulseDetected"] = (ms & 0b100) != 0
        result["improperMeasurement"] = (ms & 0b100000) != 0
        index += 1

    result["battery"] = battery[0]

    return result


async def update_device_time(
    client: BleakClient,
    device: BLEDevice,
    notify_callback=None,
):
    log.debug("  => Asking %s for the time...", client.address)
    try:
        value = await client.read_gatt_char("00002a08-0000-1000-8000-00805f9b34fb")
        year, month, day, hour, minute, second = struct.unpack("<HBBBBB", value)
        log.debug(
            "  Got time: %s-%s-%s %s:%s:%s",
            year,
            month,
            day,
            hour,
            minute,
            second,
        )

        device_time = datetime(year, month, day, hour, minute, second)
        system_time = datetime.now()

        if abs(device_time - system_time) > timedelta(seconds=60):
            log.debug("  Time is not up to date. Updating ...")
            if notify_callback:
                notify_callback(
                    "Updating time",
                    f"Updating time on {device.name} ({device.address}).",
                    5000,
                )
            new_time = struct.pack(
                "<HBBBBB",
                system_time.year,
                system_time.month,
                system_time.day,
                system_time.hour,
                system_time.minute,
                system_time.second,
            )
            await client.write_gatt_char(
                "00002a08-0000-1000-8000-00805f9b34fb", new_time
            )
            if notify_callback:
                notify_callback(
                    "Time updated",
                    f"Time updated on {device.name} ({device.address}).",
                    10000,
                )
        else:
            log.debug("  Time is already up to date.")
    except Exception as err:
        log.error(
            "  Failed to get time from, or send update to %s: %s.",
            client.address,
            err,
        )
        if notify_callback:
            notify_callback(
                "Failed to update time"
                f"Failed to get, or update time on {device.name} ({device.address}): {err}",
                5000,
            )


async def get_device_data(
    client: BleakClient,
    device: BLEDevice,
    notify_callback=None,
    store_data_callback=None,
):
    log.debug("  => Subscribing to %s BPM service...", client.address)
    if notify_callback:
        notify_callback(
            "BPM service",
            f"Subscribing to {device.name} ({device.address}) BPM service.",
        )
    try:

        def create_received_data_callback(
            sender: BleakGATTCharacteristic, data: bytearray
        ):
            decoded = decode_data(data, ["100"])

            if store_data_callback:
                if (
                    "SystolicPressure_kPa" in decoded
                    and "DiastolicPressure_kPa" in decoded
                ):
                    store_data_callback(
                        BloodPressureData(
                            data={
                                "sys": decoded["SystolicPressure_kPa"],
                                "dias": decoded["DiastolicPressure_kPa"],
                            },
                            address=device.address,
                            timestamp=time.time(),
                        )
                    )

                if (
                    "SystolicPressure_mmHg" in decoded
                    and "DiastolicPressure_mmHg" in decoded
                ):
                    store_data_callback(
                        BloodPressureData(
                            data={
                                "sys": decoded["SystolicPressure_mmHg"],
                                "dias": decoded["DiastolicPressure_mmHg"],
                            },
                            address=device.address,
                            timestamp=time.time(),
                        )
                    )

        await client.start_notify(
            "00002a35-0000-1000-8000-00805f9b34fb",
            create_received_data_callback,
        )
        await asyncio.sleep(10)
        if client.is_connected:
            log.debug("  Unsubscribing from %s BPM service...", client.address)
            await client.stop_notify("00002a35-0000-1000-8000-00805f9b34fb")
    except Exception as err:
        log.error("  Failed to subscribe to %s: %s.", client.address, err)

        if client.is_connected:
            try:
                await client.stop_notify("00002a35-0000-1000-8000-00805f9b34fb")
            except Exception as stop_notify_err:
                log.error(
                    "  Failed to unsubscribe from %s: %s.",
                    client.address,
                    stop_notify_err,
                )


async def process_supported_device(
    device: BLEDevice,
    notify_callback=None,
    disconnected_callback=None,
    store_data_callback=None,
):
    client = BleakClient(device, disconnected_callback=disconnected_callback)

    try:
        await client.connect()
    except Exception as err:
        log.error("  %s connection failed: %s", device.address, err)
        if notify_callback:
            notify_callback(
                "Connection failed",
                f"Connection to {device.name} ({device.address}) failed.",
                5000,
            )
        return

    # services = await client.get_services()
    services = client.services

    has_time_service = False
    has_bpm_service = False

    for service in services:
        for char in service.characteristics:
            if "2a35" in char.uuid:
                log.debug("  Found characteristic: %s", char.uuid)
                has_bpm_service = True
            if "2a08" in char.uuid:
                log.debug("  Found characteristic: %s", char.uuid)
                has_time_service = True

    if has_time_service:
        await update_device_time(client, device, notify_callback=notify_callback)

    if has_bpm_service:
        await get_device_data(
            client,
            device,
            notify_callback=notify_callback,
            store_data_callback=store_data_callback,
        )

    if client.is_connected:
        log.debug("  Disconnecting from %s...", device.address)
        await client.disconnect()
        log.debug("  Disconnected from %s.", device.address)


def iot_advertisement_data_callback_wrapper(
    store_data_callback=None, track_device_callback=None
):
    def iot_advertisement_data_callback(
        sender: BLEDevice, advertisement_data: AdvertisementData
    ):
        all_data: List[DataType] = []
        TYPE_KEY_DICT = {
            "HEART_RATE": "00002a37-0000-1000-8000-00805f9b34fb",
            "PRESSURE": "00002a6d-0000-1000-8000-00805f9b34fb",
            "TEMPERATURE": "00002a6e-0000-1000-8000-00805f9b34fb",
            "BATTERY_LEVEL": "0000180f-0000-1000-8000-00805f9b34fb",
            "ALERT": "00002a46-0000-1000-8000-00805f9b34fb",
        }

        if advertisement_data:
            # print(advertisement_data)
            for data_type, uuid in TYPE_KEY_DICT.items():
                # starts with ...
                match = False
                for key in advertisement_data.service_data.keys():
                    if key.startswith(uuid):
                        match = True
                        break

                if match:

                    def signed():
                        return int.from_bytes(
                            advertisement_data.service_data[uuid],
                            byteorder="little",
                            signed=True,
                        )

                    def unsigned():
                        return int.from_bytes(
                            advertisement_data.service_data[uuid],
                            byteorder="little",
                            signed=False,
                        )

                    def bytes_to_utf8():
                        try:
                            return advertisement_data.service_data[uuid].decode("utf-8")
                        except UnicodeDecodeError as err:
                            log.error(
                                "Failed to decode bytes to utf-8: %s",
                                err,
                                exc_info=True,
                            )
                            return None

                    data = None
                    if data_type == "HEART_RATE":
                        data_value = signed()
                        log.debug(
                            "  - BLE Found %s: Heart rate data: %s", uuid, data_value
                        )
                        data = HeartRateData(
                            {"rate": data_value}, sender.address, time.time()
                        )
                    elif data_type == "PRESSURE":
                        data_value = unsigned()
                        log.debug(
                            "  - BLE Found %s: Pressure data: %s", uuid, data_value
                        )
                        data = PressureData(
                            {"level": data_value}, sender.address, time.time()
                        )
                    elif data_type == "TEMPERATURE":
                        data_value = signed()
                        log.debug(
                            "  - BLE Found %s: Temperature data: %s", uuid, data_value
                        )
                        data = TemperatureData(
                            {"level": data_value}, sender.address, time.time()
                        )
                    elif data_type == "BATTERY_LEVEL":
                        data_value = signed()
                        log.debug(
                            "  - BLE Found %s: Battery level data: %s", uuid, data_value
                        )
                        data = BatteryLevelData(
                            {"level": data_value}, sender.address, time.time()
                        )
                    elif data_type == "ALERT":
                        data_value = bytes_to_utf8()
                        log.debug("  - BLE Found %s: Alert data: %s", uuid, data_value)
                        data = AlertData(
                            {"id": data_value}, sender.address, time.time()
                        )
                    all_data.append(data)

        # Check for manufacturer data
        # if advertisement_data.manufacturer_data:
        #     print(f"  Manufacturer data: {advertisement_data.manufacturer_data}")

        if len(all_data) > 0:
            if store_data_callback is not None:
                for d in all_data:
                    store_data_callback(d)

        if track_device_callback is not None:
            track_device_callback(sender)

    return iot_advertisement_data_callback
