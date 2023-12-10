import unittest
import time
from bcms.data_store import BCMSDeviceDataDB, BatteryLevelData, HeartRateData


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
