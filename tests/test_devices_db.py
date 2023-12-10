import unittest
import tempfile
import os
import json
from bcms.devices_db import BCMSDeviceDB, BCMSDevice


class TestBCMSDeviceDB(unittest.TestCase):
    def setUp(self):
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
            },
            {
                "address": "C5:DF:AE:FC:44:CB",
                "name": "Bangle.js 44cb",
                "approved": True,
                "paired": False,
            },
        ]
        with open(self.temp_file, "w") as f:
            json.dump(data, f)

        # Load the data using BCMSDeviceDB
        db = BCMSDeviceDB(self.temp_file)
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

        # Load the data using BCMSDeviceDB
        db = BCMSDeviceDB(self.temp_file)
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
                },
                {
                    "address": "C5:DF:AE:FC:44:CB",
                    "name": "Bangle.js 44cb",
                    "approved": True,
                    "paired": False,
                },
            ],
        )

    def test_add(self):
        # Create a new BCMSDeviceDB
        db = BCMSDeviceDB(self.temp_file)

        # Add a device
        device = BCMSDevice("00:09:1F:8A:BC:21", "A&D_UA-651BLE_8ABC21")
        db.add(device)

        # Check that the device was added
        self.assertEqual(db.get_all(), [device])

    def test_replace(self):
        # Create a new BCMSDeviceDB and add a device
        db = BCMSDeviceDB(self.temp_file)
        device = BCMSDevice("00:09:1F:8A:BC:21", "A&D_UA-651BLE_8ABC21")
        db.add(device)

        # Replace the device
        new_device = BCMSDevice("00:09:1F:8A:BC:21", "New Device", False, True)
        db.replace(new_device)

        # Check that the device was replaced
        self.assertEqual(db.get_all(), [new_device])

    def test_remove(self):
        # Create a new BCMSDeviceDB and add a device
        db = BCMSDeviceDB(self.temp_file)
        device = BCMSDevice("00:09:1F:8A:BC:21", "A&D_UA-651BLE_8ABC21")
        db.add(device)

        # Remove the device
        db.remove(device.address)

        # Check that the device was removed
        self.assertEqual(db.get_all(), [])


if __name__ == "__main__":
    unittest.main()
