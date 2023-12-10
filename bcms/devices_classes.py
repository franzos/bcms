import time
from dataclasses import dataclass
from typing import Union


@dataclass
class BCMSDeviceInfo:
    address: str
    name: str
    approved: bool = False
    paired: bool = False
    id: Union[None, str] = None
    is_registered: bool = False

    def __hash__(self):
        return hash(
            (
                self.address,
                self.name,
                self.approved,
                self.paired,
                self.id,
                self.is_registered,
            )
        )


@dataclass
class BCMSDeviceInfoWithLastSeen:
    address: str
    name: str
    approved: bool
    paired: bool
    id: Union[None, str] = None
    is_registered: bool = False
    last_seen: Union[None, str] = None

    def device_info(self) -> "BCMSDeviceInfo":
        return BCMSDeviceInfo(
            address=self.address,
            name=self.name,
            approved=self.approved,
            paired=self.paired,
            id=self.id,
            is_registered=self.is_registered,
        )

    def has_max_age(self, max_age_s: int) -> bool:
        if self.last_seen is None:
            return True
        return round(self.last_seen) >= round(time.time() - max_age_s)
