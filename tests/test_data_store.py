import unittest
import time
from bcms.data_store import (
    BCMSDeviceDataDB,
    BatteryLevelData,
    HeartRateData,
    limit_iot_data_sample_rate,
)


class TestBCMSDeviceDataDB(unittest.TestCase):
    def setUp(self):
        self.db = BCMSDeviceDataDB()

    def test_add_and_get_all(self):
        # Add some data
        data1 = BatteryLevelData({"level": 80}, "00:09:1F:8A:BC:21", round(time.time()))
        data2 = HeartRateData({"rate": 70}, "C5:DF:AE:FC:44:CB", round(time.time()))
        self.db.add(data1)
        self.db.add(data2)

        # Get all data
        data = self.db.get()

        # Check that the data was added and retrieved correctly
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0].data, data1.data)
        self.assertEqual(data[0].address, data1.address)
        self.assertEqual(data[1].data, data2.data)
        self.assertEqual(data[1].address, data2.address)

    def test_get_by_time(self):
        # Add some data at different times
        now = round(time.time())
        data1 = BatteryLevelData({"level": 80}, "00:09:1F:8A:BC:21", now - 100)
        data2 = HeartRateData({"rate": 70}, "C5:DF:AE:FC:44:CB", now)
        self.db.add(data1)
        self.db.add(data2)

        # Get data from the last 50 seconds
        data = self.db.get(from_time=now - 50)

        # Check that only the second piece of data was retrieved
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].data, data2.data)
        self.assertEqual(data[0].address, data2.address)

    def test_get_by_address(self):
        # Add some data for different devices
        data1 = BatteryLevelData({"level": 80}, "00:09:1F:8A:BC:21", round(time.time()))
        data2 = HeartRateData({"rate": 70}, "C5:DF:AE:FC:44:CB", round(time.time()))
        self.db.add(data1)
        self.db.add(data2)

        # Get data for the first device
        data = self.db.get(device_address="00:09:1F:8A:BC:21")

        # Check that only the first piece of data was retrieved
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].data, data1.data)
        self.assertEqual(data[0].address, data1.address)

    def test_get_by_time_and_address(self):
        # Add some data at different times for different devices
        now = round(time.time())
        data1 = BatteryLevelData({"level": 80}, "00:09:1F:8A:BC:21", now - 100)
        data2 = HeartRateData({"rate": 70}, "C5:DF:AE:FC:44:CB", now)
        self.db.add(data1)
        self.db.add(data2)

        # Get data from the last 50 seconds for the second device
        data = self.db.get(from_time=now - 50, device_address="C5:DF:AE:FC:44:CB")

        # Check that only the second piece of data was retrieved
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].data, data2.data)
        self.assertEqual(data[0].address, data2.address)


class DataTypeTest(unittest.TestCase):
    def test_limit_iot_data_sample_rate(self):
        # Create a list of DataType objects
        data = [
            BatteryLevelData({"level": 90}, "address1", 1),
            BatteryLevelData({"level": 80}, "address1", 1.5),
            BatteryLevelData({"level": 70}, "address1", 2),
            BatteryLevelData({"level": 60}, "address1", 2.5),
            BatteryLevelData({"level": 50}, "address1", 3),
            BatteryLevelData({"level": 40}, "address1", 3.5),
            BatteryLevelData({"level": 30}, "address1", 4),
            BatteryLevelData({"level": 20}, "address1", 4.5),
            BatteryLevelData({"level": 10}, "address1", 5),
        ]

        # Call the function with samples_every_seconds=2
        result = limit_iot_data_sample_rate(data, 2)

        # Check that the timestamps of the data in the result are as expected
        # (i.e., at least 2 seconds apart)
        for i in range(1, len(result)):
            self.assertGreaterEqual(result[i].timestamp - result[i - 1].timestamp, 2)
