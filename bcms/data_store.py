import sqlite3
import json
import logging
from datetime import datetime
from typing import List

from .devices_classes import BCMSDeviceInfoWithLastSeen
from .data_types import (
    DataType,
    BatteryLevelData,
    HeartRateData,
    TemperatureData,
    PressureData,
    BloodPressureData,
    AlertData,
)


log = logging.getLogger(__name__)


class BCMSDeviceDataDB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.execute(
            """
            CREATE TABLE data (
                id INTEGER PRIMARY KEY,
                type TEXT,
                data TEXT,
                address TEXT,
                timestamp INTEGER
            )
        """
        )

    def add(self, data: DataType):
        self.conn.execute(
            """
            INSERT INTO data (type, data, address, timestamp) VALUES (?, ?, ?, ?)
        """,
            (type(data).__name__, json.dumps(data.data), data.address, data.timestamp),
        )
        self.conn.commit()

    def get(
        self,
        from_time: int = None,
        to_time: int = None,
        device_address: str = None,
        limit: int = 50,
    ):
        query = "SELECT * FROM data WHERE 1"
        params = []
        if from_time is not None:
            query += " AND timestamp >= ?"
            params.append(round(from_time))
        if to_time is not None:
            query += " AND timestamp <= ?"
            params.append(round(to_time))
        if device_address is not None:
            query += " AND address = ?"
            params.append(device_address)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        cursor = self.conn.execute(query, params)

        data_objects = []
        for row in cursor.fetchall():
            id, type, data, address, timestamp = row
            if type == "BatteryLevelData":
                data_objects.append(
                    BatteryLevelData(json.loads(data), address, timestamp)
                )
            elif type == "HeartRateData":
                data_objects.append(HeartRateData(json.loads(data), address, timestamp))
            elif type == "TemperatureData":
                data_objects.append(
                    TemperatureData(json.loads(data), address, timestamp)
                )
            elif type == "PressureData":
                data_objects.append(PressureData(json.loads(data), address, timestamp))
            elif type == "BloodPressureData":
                data_objects.append(
                    BloodPressureData(json.loads(data), address, timestamp)
                )
            elif type == "AlertData":
                data_objects.append(AlertData(json.loads(data), address, timestamp))
            else:
                raise Exception(f"Unknown data type: {type}")

        return data_objects

    def clear_old_data(self, seconds: int):
        current_time = int(datetime.now().timestamp())
        threshold_time = current_time - seconds
        self.conn.execute("DELETE FROM data WHERE timestamp < ?", (threshold_time,))
        self.conn.commit()

    def clear(self):
        self.conn.execute("DELETE FROM data")
        self.conn.commit()


def dump_iot_data_for_api_submission(
    input_data: List[DataType], registered_devices: list[BCMSDeviceInfoWithLastSeen]
):
    registered_addresses = [d.address for d in registered_devices]

    # sort data by device
    data_by_device = {}
    for d in input_data:
        # check if address is registered
        if d.address not in registered_addresses:
            log.debug("Skipping unregistered device %s", d.address)
            continue

        if d.address not in data_by_device:
            data_by_device[d.address] = []
        data_by_device[d.address].append(d)

    # sort data by device and type
    data_by_device_and_type = []

    # loop through data by device
    for address, data in data_by_device.items():
        # get device ID for later assignment
        device_id = None
        for d in registered_devices:
            if d.address == address:
                device_id = d.id
                break

        data_by_type = {}
        for d in data:
            if d.name not in data_by_type:
                data_by_type[d.name] = []

            data_by_type[d.name].append({"timestamp": d.timestamp, "data": d.data})
        for type, data in data_by_type.items():
            data_by_device_and_type.append(
                {"iotDeviceId": device_id, "dataType": type, "data": data}
            )

    return data_by_device_and_type


def limit_iot_data_sample_rate(
    data: List[DataType], samples_every_seconds=2
) -> List[DataType]:
    """
    Limit the number of samples per second, per type and address
    - for ex. samples_every_seconds=2 means that only one sample per type and address, every 2 seconds, will be kept
    """
    if len(data) == 0:
        return data

    # sort data by device
    data_by_device = {}
    for d in data:
        if d.address not in data_by_device:
            data_by_device[d.address] = []
        data_by_device[d.address].append(d)

    # sort data by device and type
    data_by_device_and_type = {}
    for address, data in data_by_device.items():
        data_by_type = {}
        for d in data:
            if d.__class__.__name__ not in data_by_type:
                data_by_type[d.__class__.__name__] = []
            data_by_type[d.__class__.__name__].append(d)
        data_by_device_and_type[address] = data_by_type

    # filter data
    filtered_data = []
    for address, data_by_type in data_by_device_and_type.items():
        for type, data in data_by_type.items():
            last_timestamp = None
            for d in data:
                if (
                    last_timestamp is None
                    or d.timestamp - last_timestamp > samples_every_seconds
                ):
                    filtered_data.append(d)
                    last_timestamp = d.timestamp

    return filtered_data
