import dataclasses
import os
import json
import time
from typing import List, Union
import logging

from .config import KNOWN_DEVICES_FILE
from .devices_classes import BCMSDeviceInfo, BCMSDeviceInfoWithLastSeen


log = logging.getLogger(__name__)


class BCMDeviceMemory:
    devices: List[BCMSDeviceInfoWithLastSeen]

    def __init__(self, file_path=KNOWN_DEVICES_FILE, skip_load=False):
        self.devices = []
        self.skip_load = skip_load
        self.filepath = os.path.expanduser(file_path)
        self.load()

    def load(self):
        if self.skip_load:
            log.debug("Skipping load of devices memory")
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                # check if file is empty
                if os.stat(self.filepath).st_size == 0:
                    log.warning("Devices file is empty")
                    return

                data = json.load(file)

                # Check if data is in old format (dict), if so convert to new format (list)
                is_legacy = False
                if isinstance(data, dict):
                    data = [
                        {
                            "id": None,
                            "address": k,
                            "name": v,
                            "approved": True,
                            "paired": False,
                        }
                        for k, v in data.items()
                    ]
                    is_legacy = True

                for device in data:
                    self.devices.append(
                        BCMSDeviceInfoWithLastSeen(**device, last_seen=None)
                    )

                if is_legacy:
                    self.save()
        except FileNotFoundError:
            pass

    def save(self):
        if self.skip_load:
            log.debug("Skipping save of devices memory")
            return

        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as file:
            data = []
            for device in self.devices:
                if device.paired or device.approved:
                    log.debug("Saving device %s", device.address)
                    data.append(
                        dataclasses.asdict(
                            BCMSDeviceInfo(
                                address=device.address,
                                name=device.name,
                                approved=device.approved,
                                paired=device.paired,
                                id=device.id,
                                is_registered=device.is_registered,
                            )
                        )
                    )
                else:
                    log.debug("Skipping device %s", device.address)

            json.dump(data, file)

    def exists(self, address) -> bool:
        for device in self.devices:
            if device.address == address:
                return True
        return False

    def add(self, device: BCMSDeviceInfo):
        log.debug("+ Device %s, %s", device.name, device.address)
        self.replace(device)

    def replace(
        self,
        device: BCMSDeviceInfo,
    ):
        log.debug("= Device %s, %s", device.name, device.address)
        exists = self.get(device.address)
        if exists:
            self.remove(device.address)
        self.devices.append(
            BCMSDeviceInfoWithLastSeen(
                *device.__dict__.values(),
                last_seen=round(time.time()),
            )
        )
        if device.paired or device.approved:
            self.save()

    def update_last_seen(self, address: str):
        device = self.get(address)
        if device:
            device.last_seen = round(time.time())

    def remove(self, address: str):
        exists = self.get(address)
        if exists:
            self.devices = [x for x in self.devices if x.address != address]

            if exists.paired or exists.approved:
                self.save()

    def get(self, address: str) -> Union[BCMSDeviceInfoWithLastSeen, None]:
        for device in self.devices:
            if device.address == address:
                return device
        return None

    def get_all(self) -> list[BCMSDeviceInfoWithLastSeen]:
        return self.devices

    def get_registered(self) -> list[BCMSDeviceInfoWithLastSeen]:
        return [x for x in self.devices if x.is_registered]

    def get_approved_or_paired(
        self,
    ) -> list[BCMSDeviceInfoWithLastSeen]:
        return [x for x in self.devices if (x.approved or x.paired)]
