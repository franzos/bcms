import time
from typing import List
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


class DataType:
    def __init__(self, data, address, timestamp, name):
        self.data = data
        self.address = address
        self.timestamp = round(timestamp)
        self.name = name


class BatteryLevelData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "battery_level")
        self.level = data["level"]


class HeartRateData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "heart_rate")
        self.rate = data["rate"]


class TemperatureData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "temperature")
        self.level = data["level"]


class PressureData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "pressure")
        self.level = data["level"]


class BloodPressureData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "blood_pressure")
        self.sys = data["sys"]
        self.dias = data["dias"]


class HumidityData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "humidity")
        self.level = data["level"]


class AlertData(DataType):
    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "alert")
        self.id = data["id"]
