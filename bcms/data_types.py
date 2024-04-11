"""Data types related to collection and submission"""


class DataType:
    """Generic type"""

    def __init__(self, data, address, timestamp, name):
        self.data = data
        self.address = address
        self.timestamp = round(timestamp)
        """name of the data type"""
        self.name = name


class BatteryLevelData(DataType):
    """Battery level data type"""

    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "battery_level")
        self.level = data["level"]


class HeartRateData(DataType):
    """Heart rate data type"""

    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "heart_rate")
        self.rate = data["rate"]


class TemperatureData(DataType):
    """Temperature data type"""

    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "temperature")
        self.level = data["level"]


class PressureData(DataType):
    """Pressure data type"""

    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "pressure")
        self.level = data["level"]


class BloodPressureData(DataType):
    """Blood pressure data type"""

    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "blood_pressure")
        self.sys = data["sys"]
        self.dias = data["dias"]

    # For unit testing
    def __eq__(self, other):
        if isinstance(other, BloodPressureData):
            return (
                self.data == other.data
                and self.address == other.address
                and self.timestamp == other.timestamp
            )
        return False


class HumidityData(DataType):
    """Humidity data type"""

    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "humidity")
        self.level = data["level"]


class AlertData(DataType):
    """Alert data type"""

    def __init__(self, data, address, timestamp):
        super().__init__(data, address, timestamp, "alert")
        self.id = data["id"]
