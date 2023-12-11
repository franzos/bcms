import pkg_resources
import capnp
import os


RPC_ADDRESS = "127.0.0.1"
RPC_PORT = 4567

BLOOD_PRESSURE_DATA_FILE = "/tmp/bluetooth-client-manager-service-data.txt"

KNOWN_DEVICES_FILE = os.path.expanduser(
    "~/.local/share/bluetooth-client-manager-service/device.json"
)

CAPNP_INTERFACE = pkg_resources.resource_filename(__name__, "rpc/bcms.capnp")

pimstore_capnp = capnp.load(CAPNP_INTERFACE)
device_capnp = pimstore_capnp.BCMSDeviceInfo
working_mode_capnp = pimstore_capnp.BCMSWorkingMode


LOG_FILE_PATH = os.path.expanduser(
    "~/.local/share/bluetooth-client-manager-service/log"
)
LOG_NAME = "bcms"

SUPPORTED_DEVICES = ["A&D_UA-651BLE_", "BLESmart_", "X4 Smart"]
