import os
import json
import time
from dataclasses import dataclass
import dataclasses
from typing import Union

from .config import KNOWN_DEVICES_FILE

# For RPC and in-memory usage


@dataclass
class BCMSDeviceInfo:
    address: str
    name: str
    approved: bool
    paired: bool

    def __hash__(self):
        return hash((self.address, self.name, self.approved, self.paired))


@dataclass
class BCMSDeviceInfoWithLastSeen:
    address: str
    name: str
    approved: bool
    paired: bool
    last_seen: int

    def device_info(self) -> "BCMSDeviceInfo":
        return BCMSDeviceInfo(
            address=self.address,
            name=self.name,
            approved=self.approved,
            paired=self.paired,
        )

    def has_max_age(self, max_age_s: int) -> bool:
        return round(self.last_seen) >= round(time.time() - max_age_s)


@dataclass
class BCMSDevice:
    address: str
    name: str
    approved: bool = True
    paired: bool = False


class BCMSDeviceDB:
    """Tracks all approved AND paired devices"""

    cache: list[BCMSDevice]

    def __init__(self, file_path=KNOWN_DEVICES_FILE):
        self.filepath = os.path.expanduser(file_path)
        self.cache = []
        self.load()

    def load(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = json.load(file)

                # Check if data is in old format (dict), if so convert to new format (list)
                is_legacy = False
                if isinstance(data, dict):
                    data = [
                        {"address": k, "name": v, "approved": True, "paired": False}
                        for k, v in data.items()
                    ]
                    is_legacy = True

                for device in data:
                    self.cache.append(BCMSDevice(**device))

                if is_legacy:
                    self.save()
        except FileNotFoundError:
            pass

    def save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as file:
            data = []
            for device in self.cache:
                data.append(dataclasses.asdict(device))

            json.dump(data, file)

    def exists(self, address: str) -> Union[BCMSDevice, None]:
        for device in self.cache:
            if device.address == address:
                return device
        return None

    def add(self, device: BCMSDevice):
        if not self.exists(device.address):
            self.cache.append(device)
            self.save()

    def replace(self, device: BCMSDevice):
        if self.exists(device.address):
            self.cache = [x for x in self.cache if x.address != device.address]
            self.cache.append(device)
            self.save()

    def remove(self, address: str):
        for device in self.cache:
            if device.address == address:
                self.cache = [x for x in self.cache if x.address != address]
                self.save()
        return True

    def get(self, address) -> Union[BCMSDevice, None]:
        for device in self.cache:
            if device.address == address:
                return device
        return None

    def get_all(self) -> list[BCMSDevice]:
        return self.cache
