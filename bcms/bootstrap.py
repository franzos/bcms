from bleak import BleakClient
from bleak.exc import BleakDeviceNotFoundError
import logging
import subprocess

from .queue import AsyncQueue
from .paired_devices import get_paired_devices
from .devices_memory import BCMDeviceMemory
from .data_store import BCMSDeviceDataDB
from .devices_classes import BCMSDeviceInfo
from .api import BackendAPI


log = logging.getLogger(__name__)


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
        if paired:
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

    return filtered_devices


def approve_device(device_address: str, success_callback=None, notify_callback=None):
    """
    Approve a device
        - Approval does not imply pairing
    """
    log.debug("=> Approving %s", device_address)

    exists = devices_mem.get(device_address)
    name = exists and exists.name or ""

    if not exists:
        raise Exception("Device not found")

    if exists and exists.approved:
        raise Exception("Device already approved")

    if exists:
        # existing device; approved but not paired by default
        devices_mem.replace(
            BCMSDeviceInfo(
                address=device_address,
                name=exists.name,
                approved=True,
                paired=exists.paired,
                id=exists.id,
                is_registered=exists.is_registered,
            ),
        )
    else:
        # new device; approved but not paired by default
        devices_mem.add(
            BCMSDeviceInfo(
                address=device_address, name=name, approved=True, paired=False
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
    name = exists and exists.name or ""

    if not exists:
        raise Exception("Device not found")

    if exists and exists.paired:
        raise Exception("Cannot remove paired device. Unpair first.")
    else:
        devices_mem.remove(device_address)
        log.debug("   Removed %s", device_address)

        if notify_callback:
            notify_callback("Removed successfully", f"Removed {device_address}", 5000)

        return True


async def pair_device(device_address: str, success_callback=None, notify_callback=None):
    """
    Pair a device
        - Pairing applies approval
    """
    if notify_callback:
        notify_callback(
            "Pairing", f"Requesting to pair with {device_address} ...", 5000
        )
    async with BleakClient(device_address) as client:
        log.debug("=> Requesting to pair %s", device_address)

        success = await client.pair()
        if success:
            log.debug("   Paired %s", device_address)
            exists = devices_mem.get(device_address)
            if exists:
                # existing device; approved and paired by default
                devices_mem.replace(
                    BCMSDeviceInfo(
                        address=device_address,
                        name=exists.name,
                        approved=True,
                        paired=True,
                        id=exists.id,
                        is_registered=exists.is_registered,
                    )
                )
            else:
                # new device; approved and paired by default
                devices_mem.add(
                    BCMSDeviceInfo(
                        address=device_address,
                        name="",
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


async def unpair_subprocess(device_address: str) -> bool:
    try:
        # bluetoothctl remove 00:09:1F:8A:BC:21
        result = subprocess.run(
            ["bluetoothctl", "remove", device_address], capture_output=True, check=False
        )
        # bluetoothctl untrust 00:09:1F:8A:BC:21
        subprocess.run(["bluetoothctl", "untrust", device_address], check=False)

        if result.returncode == 0:
            return True
        else:
            return False
    except Exception:
        return False


async def unpair_device(device_address: str, notify_callback=None):
    """Unpair a device"""
    if notify_callback:
        notify_callback(
            "Unpair", f"Requesting to unpair frpm {device_address} ...", 5000
        )
    log.info("=> Requesting to unpair %s", device_address)

    exists = devices_mem.get(device_address)

    if exists is None:
        await unpair_subprocess(device_address)
        raise Exception("Device not found")

    try:
        async with BleakClient(device_address, timeout=15) as client:
            # if exists and not exists.paired or exists_db and not exists_db.paired:
            #     raise Exception("Cannot unpair unpaired device.")

            success = await client.unpair()

            if success:
                # This is probably unnecessary, but just in case
                await unpair_subprocess(device_address)

                devices_mem.remove(device_address)
                log.debug("Removed %s", device_address)

                if notify_callback:
                    notify_callback(
                        "Unpaired successfully", f"Unpaired from {device_address}", 5000
                    )
            else:
                log.error("   Failed to unpair %s", device_address)
                if notify_callback:
                    notify_callback(
                        "Failed to unpair",
                        f"Failed to unpair from {device_address}",
                        5000,
                    )
    except BleakDeviceNotFoundError:
        # Assume the device has been removed from the OS
        devices_mem.remove(device_address)
        log.debug("Removed %s", device_address)

        if notify_callback:
            notify_callback(
                "Unpaired successfully", f"Unpaired from {device_address}", 5000
            )

    except Exception as e:
        # Try an alternative method
        log.error("Failed to unpair %s: %s", device_address, e)
        log.info("Trying to unpair %s with bluetoothctl", device_address)
        success_manual = await unpair_subprocess(device_address)
        if success_manual:
            devices_mem.remove(device_address)
            log.debug("Removed %s", device_address)

            if notify_callback:
                notify_callback(
                    "Unpaired successfully", f"Unpaired from {device_address}", 5000
                )
        else:
            log.error("Failed to unpair %s: %s", device_address, e)
            if notify_callback:
                notify_callback(
                    "Failed to unpair",
                    f"Failed to unpair from {device_address}: {e}",
                    5000,
                )
            raise e


def is_paired_device(device_address: str):
    """Check if a device is paired"""
    return devices_mem.exists(device_address)
