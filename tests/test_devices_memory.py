import unittest
from bcms.devices_memory import BCMDeviceMemory
from bcms.devices_db import BCMSDeviceInfo


class TestBCMDeviceMemory(unittest.TestCase):
    def setUp(self):
        self.memory = BCMDeviceMemory()

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
