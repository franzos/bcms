import unittest
from unittest.mock import Mock

from bcms.rpc_client import BCMSClient


class TestBCMSClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Create a mock BCMS server
        self.mock_bcms = Mock()

        # Create a mock BCMSNetworkManager
        self.mock_network_manager = Mock()
        self.mock_network_manager.get_bcms.return_value = self.mock_bcms

        # Create the BCMSClient
        self.client = BCMSClient(self.mock_network_manager)

    async def test_list(self):
        # Set up the mock server to return a specific result
        self.mock_bcms.list.return_value.a_wait.return_value = ["device1", "device2"]

        # Call the list method and check the result
        result = self.client.list(True)
        self.assertEqual(result, ["device1", "device2"])

    async def test_approve(self):
        self.mock_bcms.approve.return_value.a_wait.return_value = (True, [])
        result = self.client.approve("device1")
        self.assertEqual(result, (True, []))

    async def test_remove(self):
        self.mock_bcms.remove.return_value.a_wait.return_value = (True, [])
        result = self.client.remove("device1")
        self.assertEqual(result, (True, []))

    async def test_pair(self):
        self.mock_bcms.pair.return_value.a_wait.return_value = (True, [])
        result = self.client.pair("device1")
        self.assertEqual(result, (True, []))

    async def test_unpair(self):
        self.mock_bcms.unpair.return_value.a_wait.return_value = (True, [])
        result = self.client.unpair("device1")
        self.assertEqual(result, (True, []))

    async def test_is_paired(self):
        self.mock_bcms.isPaired.return_value.a_wait.return_value = (True, [])
        result = self.client.is_paired("device1")
        self.assertEqual(result, (True, []))

    # Add similar tests for the other methods...


if __name__ == "__main__":
    unittest.main()
