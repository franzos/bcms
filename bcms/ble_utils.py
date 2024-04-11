import time
from typing import List
import asyncio
import struct
import logging
from datetime import datetime, timedelta
from bleak import BleakClient, BleakGATTCharacteristic
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

from .data_types import (
    BloodPressureData,
    DataType,
    TemperatureData,
    BatteryLevelData,
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


async def process_supported_device(
    device: BLEDevice,
    notify_callback=None,
    disconnected_callback=None,
    store_data_callback=None,
    retry_count=0,
):
    def create_received_data_callback(sender: BleakGATTCharacteristic, data: bytearray):
        log.info("Received data from %s BPM service.", client.address)
        if notify_callback:
            notify_callback(
                "BPM service",
                f"Received data from %s BPM service {client.address}.",
                10000,
            )
        decoded = decode_data(data, ["100"])

        if store_data_callback:
            if "SystolicPressure_kPa" in decoded and "DiastolicPressure_kPa" in decoded:
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

    try:
        async with BleakClient(
            device,
            disconnected_callback=disconnected_callback,
        ) as client:
            for service in client.services:
                for char in service.characteristics:
                    if "read" in char.properties:
                        if char.uuid == "00002a19-0000-1000-8000-00805f9b34fb":
                            value = bytes(await client.read_gatt_char(char.uuid))
                            log.debug("battery", value)
                        elif char.uuid == "00002a35-0000-1000-8000-00805f9b34fb":
                            value = bytes(await client.read_gatt_char(char.uuid))
                            log.debug("serial", value)

                    if char.uuid == "00002a08-0000-1000-8000-00805f9b34fb":
                        value = await client.read_gatt_char(char.uuid)
                        year, month, day, hour, minute, second = struct.unpack(
                            "<HBBBBB", value
                        )
                        log.debug(
                            "Got time: %s-%s-%s %s:%s:%s",
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
                            log.debug("Time is not up to date. Updating ...")
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
                            log.info(
                                "Updated time on %s (%s)", device.name, device.address
                            )
                            if notify_callback:
                                notify_callback(
                                    "Time updated",
                                    f"Time updated on {device.name} ({device.address}).",
                                    10000,
                                )
                            await asyncio.sleep(0.1)

                    if char.uuid == "00002a35-0000-1000-8000-00805f9b34fb":
                        log.debug("Found BPM service: %s", char.uuid)
                        if notify_callback:
                            notify_callback(
                                "Blood Presure Measurement",
                                f"Subscribing on {device.name} ({device.address}).",
                                10000,
                            )
                        await client.start_notify(char, create_received_data_callback)
                        await asyncio.sleep(5.0)
                        # await client.stop_notify(char)

            if notify_callback:
                notify_callback(
                    "Done",
                    f"Disconnecting from {device.name} ({device.address}) ...",
                    10000,
                )

    # if timeout error, retry max 3 times
    except asyncio.TimeoutError as err:
        log.error("TimeoutError: %s", err)
        if notify_callback:
            notify_callback(
                "TimeoutError",
                f"TimeoutError on {device.name} ({device.address}).",
                10000,
            )
        if retry_count < 3:
            log.debug("Retrying connection...%d", retry_count)
            await asyncio.sleep(0.1)
            await process_supported_device(
                device,
                notify_callback=notify_callback,
                disconnected_callback=disconnected_callback,
                store_data_callback=store_data_callback,
                retry_count=retry_count + 1,
            )
        else:
            raise err

    except Exception as err:
        log.error("Exception: %s", err)
        raise err


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
