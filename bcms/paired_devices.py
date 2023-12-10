import dbus
import logging

from .devices_db import BCMSDeviceInfo


log = logging.getLogger(__name__)


def get_paired_devices():
    """Get paired devices from dbus"""
    BUS_NAME = "org.bluez"
    DEVICE_INTERFACE = BUS_NAME + ".Device1"
    bus = dbus.SystemBus()
    try:
        obj = bus.get_object(BUS_NAME, "/")
    except Exception:
        log.error("Failed to connect to %s on dbus. Is bluetoothd running?", BUS_NAME)
        return None
    manager = dbus.Interface(obj, "org.freedesktop.DBus.ObjectManager")
    paired_devices = set()
    for _, ifaces in manager.GetManagedObjects().items():
        device = ifaces.get(DEVICE_INTERFACE)
        if device and device["Paired"]:
            approved = False
            if device["Paired"]:
                approved = True

            device_info = BCMSDeviceInfo(
                device["Address"],
                device["Name"],
                approved,
                device["Paired"],
            )
            paired_devices.add(device_info)
    return paired_devices
