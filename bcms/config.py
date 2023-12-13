import pkg_resources
import capnp
import os


DATA_SUBMISSION_INTERVAL = 30.0
CLEAR_IOT_DATA_CACHE_INTERVAL = 180.0
BLUETOOTH_SCAN_INTERVAL = 5.0

SUPPORTED_DEVICES = ["A&D_UA-651BLE_", "BLESmart_", "X4 Smart"]

# RPC
RPC_ADDRESS = "127.0.0.1"
RPC_PORT = 4567

CAPNP_INTERFACE = pkg_resources.resource_filename(__name__, "rpc/bcms.capnp")

pimstore_capnp = capnp.load(CAPNP_INTERFACE)
device_capnp = pimstore_capnp.BCMSDeviceInfo
working_mode_capnp = pimstore_capnp.BCMSWorkingMode

# LOG
LOG_NAME = "bcms"

# LEGACY
KNOWN_DEVICES_FILE = os.path.expanduser(
    "~/.local/share/bluetooth-client-manager-service/device.json"
)
