import sqlite3
import json
from datetime import datetime

from .data_types import (
    DataType,
    BatteryLevelData,
    HeartRateData,
    TemperatureData,
    PressureData,
    BloodPressureData,
    AlertData,
)


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
                data_objects.append(DataType(json.loads(data), address, timestamp))

        return data_objects

    def clear_old_data(self, seconds: int):
        current_time = int(datetime.now().timestamp())
        threshold_time = current_time - seconds
        self.conn.execute("DELETE FROM data WHERE timestamp < ?", (threshold_time,))
        self.conn.commit()

    def clear(self):
        self.conn.execute("DELETE FROM data")
        self.conn.commit()
