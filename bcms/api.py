import time
import requests
import logging
from typing import Union
from dataclasses import dataclass
from vhh_bluetooth_terminal_assigned_user import (
    get_well_known_by_identifier,
    get_well_known,
    make_bearer_headers,
)

from .config import WELL_KNOWN_SERVICE_IDENTIFIER


log = logging.getLogger(__name__)


@dataclass
class IotDeviceExistsResponse:
    """Response for iot_device_exists"""

    exists: bool
    rememberDevice: bool


@dataclass
class IotDeviceCreateResponse:
    """Response for create_iot_device"""

    hardwareIdentifier: str
    model: str
    connectionType: str
    connectionMeta: dict
    supportedDataTypes: list
    id: str
    createdAt: str
    modifiedAt: str
    revision: int


class BackendAPI:
    is_loaded = False

    auth_host = Union[None, str]
    app_host = Union[None, str]
    identifier = Union[None, str]
    device_id = Union[None, str]

    well_known = Union[None, dict]
    access_token = Union[None, str]
    access_token_expires_at = Union[None, int]

    def __init__(self) -> None:
        self.is_loaded = False

    def load(self, identifier: str = WELL_KNOWN_SERVICE_IDENTIFIER):
        from px_device_identity import is_superuser_or_quit

        log.info("Loading API with identifier %s" % identifier)
        is_superuser_or_quit()
        self.identifier = identifier
        self.refresh_well_known()
        self.is_loaded = True

    def renew_token(self):
        """Renew access token"""
        from px_device_identity import Device

        now = round(time.time())
        if (
            self.access_token is None
            or self.access_token_expires_at is None
            or self.access_token_expires_at < now
        ):
            device = Device()
            result = device.get_access_token()

            self.auth_host = device.properties.host
            self.access_token = result["access_token"]
            self.access_token_expires_at = result["expires_at"]

    def refresh_well_known(self):
        """Refresh well known"""
        from px_device_identity import Device

        device = Device()
        well_known_list = get_well_known(device)
        well_known = get_well_known_by_identifier(
            well_known=well_known_list, identifier=self.identifier
        )

        if well_known is None:
            log.warn("No well known found for %s" % self.identifier)
            return None

        self.app_host = well_known["data"].hostname

    def submit_iot_data(self, data: list):
        """Submit iot data to server"""
        if self.app_host is None:
            log.warn("No app host found")
            return None
        self.renew_token()

        url = f"{self.app_host}/api/iot-devices/data/submit"
        res = requests.post(
            url, json=data, headers=make_bearer_headers(self.access_token)
        )
        print(res.json())

    def iot_device_exists(self, address: str):
        """Check if iot device exists"""
        if self.app_host is None:
            log.warn("No app host found")
            return None
        self.renew_token()

        url = f"{self.auth_host}/api/iot-devices/exists"
        res = requests.post(
            url,
            json={"hardwareIdentifier": address},
            headers=make_bearer_headers(self.access_token),
        )
        return IotDeviceExistsResponse(**res.json())

    def create_iot_device(self, address: str):
        """Create iot device"""
        url = f"{self.auth_host}/api/iot-devices"
        data = {
            "hardwareIdentifier": address,
            "model": "generic",
            "connectionType": "bluetooth_le",
            "connectionMeta": {},
            "supportedDataTypes": [],
        }
        res = requests.post(
            url, json=data, headers=make_bearer_headers(self.access_token)
        )
        return res.json()

    def create_iot_device_if_not_exists(self, address: str):
        """Create iot device if not exists"""
        exists = self.iot_device_exists(address)
        if exists.exists:
            return exists
        else:
            return self.create_iot_device(address)

    def last_iot_device_data_submission(self, iot_device_id: str) -> int:
        """Get last iot device data submission timestamp"""
        url = f"{self.auth_host}/api/iot-devices/{iot_device_id}/last-data-submission"
        res = requests.get(url, headers=make_bearer_headers(self.access_token))
        return res.json()
