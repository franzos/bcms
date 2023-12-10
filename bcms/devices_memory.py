import time
from typing import List, Union
import logging

from .devices_db import BCMSDeviceInfo, BCMSDeviceInfoWithLastSeen


log = logging.getLogger(__name__)


class BCMDeviceMemory:
    devices: List[BCMSDeviceInfoWithLastSeen]

    def __init__(self):
        self.devices = []

    def exists(self, address) -> bool:
        for device in self.devices:
            if device.address == address:
                return True
        return False

    def add(self, device: BCMSDeviceInfo):
        log.debug("+ Device %s, %s", device.name, device.address)
        self.replace(device)

    def replace(self, device: BCMSDeviceInfo):
        log.debug("= Device %s, %s", device.name, device.address)
        if self.exists(device.address):
            self.remove(device.address)
        self.devices.append(
            BCMSDeviceInfoWithLastSeen(
                address=device.address,
                name=device.name,
                approved=device.approved,
                paired=device.paired,
                last_seen=round(time.time()),
            )
        )

    def remove(self, address: str):
        if self.exists(address):
            self.devices = [x for x in self.devices if x.address != address]

    def get(self, address: int) -> Union[BCMSDeviceInfoWithLastSeen, None]:
        for device in self.devices:
            if device.address == address:
                return device
        return None

    def get_all(self) -> list[BCMSDeviceInfoWithLastSeen]:
        return self.devices
