import unittest
import tempfile
import os
import json
from bcms.devices_memory import BCMDeviceMemory
from bcms.devices_classes import (
    BCMSDeviceInfo,
    BCMSDeviceInfo,
)


class TestBCMDeviceMemory(unittest.TestCase):
    def setUp(self):
        self.memory = BCMDeviceMemory(skip_load=True)
        self.maxDiff = None

    def test_add(self):
        # Add a device
        device = BCMSDeviceInfo(
            "00:09:1F:8A:BC:21", "A&D_UA-651BLE_8ABC21", True, False
        )
        self.memory.add(device)

        # Check that the device was added
        devices = self.memory.get_all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].device_info(), device)

    def test_replace(self):
        # Add a device
        device = BCMSDeviceInfo(
            "00:09:1F:8A:BC:21", "A&D_UA-651BLE_8ABC21", True, False
        )
        self.memory.add(device)

        # Replace the device
        new_device = BCMSDeviceInfo("00:09:1F:8A:BC:21", "New Device", False, True)
        self.memory.replace(new_device)

        # Check that the device was replaced
        devices = self.memory.get_all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].device_info(), new_device)

    def test_remove(self):
        # Add a device
        device = BCMSDeviceInfo(
            "00:09:1F:8A:BC:21", "A&D_UA-651BLE_8ABC21", True, False
        )
        self.memory.add(device)

        # Remove the device
        self.memory.remove(device.address)

        # Check that the device was removed
        self.assertEqual(self.memory.get_all(), [])


class TestBCMSDeviceDB(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "devices.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_new_format(self):
        # Write some data in the new format to the temp file
        data = [
            {
                "address": "00:09:1F:8A:BC:21",
                "name": "A&D_UA-651BLE_8ABC21",
                "approved": True,
                "paired": False,
                "id": None,
                "is_registered": False,
            },
            {
                "address": "C5:DF:AE:FC:44:CB",
                "name": "Bangle.js 44cb",
                "approved": True,
                "paired": False,
                "id": None,
                "is_registered": False,
            },
        ]
        with open(self.temp_file, "w") as f:
            json.dump(data, f)

        # Load the data using BCMDeviceMemory
        db = BCMDeviceMemory(file_path=self.temp_file)
        devices = db.get_all()

        # Check that the data was loaded correctly
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].address, "00:09:1F:8A:BC:21")
        self.assertEqual(devices[0].name, "A&D_UA-651BLE_8ABC21")
        self.assertEqual(devices[0].approved, True)
        self.assertEqual(devices[0].paired, False)

    def test_old_format(self):
        # Write some data in the old format to the temp file
        data = {
            "00:09:1F:8A:BC:21": "A&D_UA-651BLE_8ABC21",
            "C5:DF:AE:FC:44:CB": "Bangle.js 44cb",
        }
        with open(self.temp_file, "w") as f:
            json.dump(data, f)

        # Load the data using BCMDeviceMemory
        db = BCMDeviceMemory(file_path=self.temp_file)
        devices = db.get_all()

        # Check that the data was loaded and converted correctly
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].address, "00:09:1F:8A:BC:21")
        self.assertEqual(devices[0].name, "A&D_UA-651BLE_8ABC21")
        self.assertEqual(devices[0].approved, True)
        self.assertEqual(devices[0].paired, False)

        # Check that the data was saved in the new format
        with open(self.temp_file, "r") as f:
            saved_data = json.load(f)
        self.assertEqual(
            saved_data,
            [
                {
                    "address": "00:09:1F:8A:BC:21",
                    "name": "A&D_UA-651BLE_8ABC21",
                    "approved": True,
                    "paired": False,
                    "id": None,
                    "is_registered": False,
                },
                {
                    "address": "C5:DF:AE:FC:44:CB",
                    "name": "Bangle.js 44cb",
                    "approved": True,
                    "paired": False,
                    "id": None,
                    "is_registered": False,
                },
            ],
        )

    def test_remove(self):
        # Create a new BCMDeviceMemory and add a device
        db = BCMDeviceMemory(file_path=self.temp_file)
        device = BCMSDeviceInfo("00:09:1F:8A:BC:21", "A&D_UA-651BLE_8ABC21")
        db.add(device)

        # Remove the device
        db.remove(device.address)

        # Check that the device was removed
        self.assertEqual(db.get_all(), [])


if __name__ == "__main__":
    unittest.main()
