import time
from typing import List
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


class DataType:
    def __init__(self, data, address, timestamp):
        self.data = data
        self.address = address
        self.timestamp = round(timestamp)


class BatteryLevelData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp)
        self.level = data["level"]


class HeartRateData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp)
        self.rate = data["rate"]


class TemperatureData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp)
        self.level = data["level"]


class PressureData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp)
        self.level = data["level"]


class BloodPressureData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp)
        self.sys = data["sys"]
        self.dias = data["dias"]


class HumidityData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp)
        self.level = data["level"]


class AlertData(DataType):
    def __init__(self, data, address, timestamp=time.time()):
        super().__init__(data, address, timestamp)
        self.id = data["id"]


def dump_iot_data_for_api_submission(data: List[DataType]):
    # sort data by device
    data_by_device = {}
    for d in data:
        if d.address not in data_by_device:
            data_by_device[d.address] = []
        data_by_device[d.address].append(d)

    # sort data by device and type
    data_by_device_and_type = []

    for address, data in data_by_device.items():
        data_by_type = {}
        for d in data:
            if d.__class__.__name__ not in data_by_type:
                data_by_type[d.__class__.__name__] = []

            data_by_type[d.__class__.__name__].append(
                {"timestamp": d.timestamp, "data": d.data}
            )
        for type, data in data_by_type.items():
            data_by_device_and_type.append(
                {"iotDeviceId": address, "dataType": type, "data": data}
            )

    return data_by_device_and_type


def iot_advertisement_data_callback_wrapper(
    store_data_callback=None, track_device_callback=None
):
    def iot_advertisement_data_callback(
        sender: BLEDevice, advertisement_data: AdvertisementData
    ):
        all_data: List[DataType] = []

        if advertisement_data:
            # Check for temperature service
            temp_uuid = "00002a6e-0000-1000-8000-00805f9b34fb"
            if temp_uuid in advertisement_data.service_data:
                temp_data = (
                    int.from_bytes(
                        advertisement_data.service_data[temp_uuid],
                        byteorder="little",
                        signed=True,
                    )
                    * 1
                )
                data = TemperatureData(
                    {"level": temp_data}, sender.address, time.time()
                )
                # print(f"  Temperature data: {data.address}: {data.data}")
                all_data.append(data)

            # Check for battery service
            battery_uuid = "0000180f-0000-1000-8000-00805f9b34fb"
            if battery_uuid in advertisement_data.service_data:
                battery_data = int.from_bytes(
                    advertisement_data.service_data[battery_uuid], byteorder="little"
                )
                # print(f"  Battery data: {data.address}: {data.data}")
                data = BatteryLevelData(
                    {"level": battery_data}, sender.address, time.time()
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
