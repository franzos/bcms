from bleak import BleakClient
import logging

from .queue import AsyncQueue
from .paired_devices import get_paired_devices
from .devices_db import BCMSDeviceDB
from .devices_memory import BCMDeviceMemory
from .data_store import BCMSDeviceDataDB
from .devices_db import BCMSDevice, BCMSDeviceInfo
from .api import BackendAPI


log = logging.getLogger(__name__)


# Devices we track
devices_db = BCMSDeviceDB()
# Devices in range
devices_mem = BCMDeviceMemory()
# Devices data
devices_data = BCMSDeviceDataDB()

# Devices runtime data
# - auth_host
# - api_host
runtime_data = {}

backend_api = BackendAPI()

async_queue = AsyncQueue()


def list_devices(max_age_s=60, only_approved=False):
    """List devices that have been seen in the last max_age_s seconds"""
    devices = devices_mem.get_all()
    paired = None
    try:
        paired = get_paired_devices()
    except Exception as e:
        log.error("Failed to get paired devices %s", e)
        paired = []

    log.debug("Found devices %s", len(devices))
    filtered_devices = []
    for device in devices:
        for p in paired:
            if p.address == device.address:
                device.approved = True
                device.paired = True
                break
        if only_approved:
            if not device.approved or device.paired:
                log.debug(" - Skipping (only_approved) %s", device.address)
                continue

        if device.has_max_age(max_age_s) or device.approved or device.paired:
            filtered_devices.append(device)
        log.debug(" - Skipping (last_seen) %s", device.address)

    print("Filtered devices", len(filtered_devices))
    return filtered_devices


def approve_device(device_address: str, success_callback=None, notify_callback=None):
    """
    Approve a device
        - Approval does not imply pairing
    """
    log.debug("=> Approving %s", device_address)

    exists = devices_mem.get(device_address)
    exists_db = devices_db.exists(device_address)
    name = exists and exists.name or ""

    if not exists:
        raise Exception("Device not found")

    if exists and exists.approved or exists_db and exists_db.approved:
        raise Exception("Device already approved")

    if exists:
        # existing device; approved but not paired by default
        devices_mem.replace(
            BCMSDeviceInfo(
                address=device_address, name=name, approved=True, paired=exists.paired
            )
        )
    else:
        # new device; approved but not paired by default
        devices_mem.add(
            BCMSDeviceInfo(
                address=device_address, name=name, approved=True, paired=False
            )
        )

    if exists_db:
        # existing device; approved but not paired by default
        devices_db.replace(
            BCMSDevice(
                address=device_address,
                name=name,
                approved=True,
                paired=exists_db.paired,
            )
        )
    else:
        # new device; approved but not paired by default
        devices_db.add(
            BCMSDevice(
                address=device_address,
                name=name,
                approved=True,
                paired=False,
            )
        )

    if notify_callback:
        notify_callback("Approval successfully", f"Approved {device_address}", 5000)

    if success_callback:
        success_callback(device_address)

    return True


def remove_device(device_address: str, notify_callback=None):
    """
    Remove a device
        - Remove only, if not paired
    """
    log.debug("=> Removing %s", device_address)

    exists = devices_mem.get(device_address)
    exists_db = devices_db.exists(device_address)
    name = exists and exists.name or ""

    if not exists_db:
        raise Exception("Device not found")

    if exists and exists.paired or exists_db and exists_db.paired:
        raise Exception("Cannot remove paired device. Unpair first.")
    else:
        devices_mem.remove(device_address)
        devices_db.remove(device_address)
        log.debug("   Removed %s", device_address)

        if notify_callback:
            notify_callback("Removed successfully", f"Removed {device_address}", 5000)

        return True


async def pair_device(device_address: str, success_callback=None, notify_callback=None):
    """
    Pair a device
        - Pairing applies approval
    """
    async with BleakClient(device_address) as client:
        log.debug("=> Requesting to pair %s", device_address)

        success = await client.pair()
        if success:
            log.debug("   Paired %s", device_address)
            exists = devices_mem.get(device_address)
            name = exists and exists.name or ""
            if exists:
                # existing device; approved and paired by default
                devices_mem.replace(
                    BCMSDeviceInfo(
                        address=device_address,
                        name=name,
                        approved=True,
                        paired=True,
                    )
                )
            else:
                # new device; approved and paired by default
                devices_mem.add(
                    BCMSDeviceInfo(
                        address=device_address,
                        name=name,
                        approved=True,
                        paired=True,
                    )
                )

            exists_db = devices_db.exists(device_address)
            if exists_db:
                # existing device; approved and paired by default
                devices_db.replace(
                    BCMSDevice(
                        address=device_address,
                        name=name,
                        approved=True,
                        paired=True,
                    )
                )
            else:
                # new device; approved and paired by default
                devices_db.add(
                    BCMSDevice(
                        address=device_address,
                        name=name,
                        approved=True,
                        paired=True,
                    )
                )

            if notify_callback:
                notify_callback(
                    "Paired successfully", f"Paired with {device_address}", 5000
                )

            if success_callback:
                success_callback(device_address)

        else:
            log.error("   Failed to pair %s", device_address)
            if notify_callback:
                notify_callback(
                    "Failed to pair", f"Failed to pair with {device_address}", 5000
                )


async def unpair_device(device_address: str, notify_callback=None):
    """Unpair a device"""
    async with BleakClient(device_address) as client:
        log.debug("=> Requesting to unpair %s", device_address)

        exists = devices_mem.get(device_address)
        exists_db = devices_db.exists(device_address)
        name = exists and exists.name or ""

        if not exists_db:
            raise Exception("Device not found")

        # if exists and not exists.paired or exists_db and not exists_db.paired:
        #     raise Exception("Cannot unpair unpaired device.")

        success = await client.unpair()
        if success:
            log.debug("   Unpaired %s", device_address)
            devices_mem.remove(device_address)
            devices_db.remove(device_address)
            log.debug("   Removed %s", device_address)

            if notify_callback:
                notify_callback(
                    "Unpaired successfully", f"Unpaired with {device_address}", 5000
                )
        else:
            log.error("   Failed to unpair %s", device_address)
            if notify_callback:
                notify_callback(
                    "Failed to unpair", f"Failed to unpair with {device_address}", 5000
                )


def is_paired_device(device_address: str):
    """Check if a device is paired"""
    return devices_db.exists(device_address)
