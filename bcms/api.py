import time
import requests
import logging
from typing import Union
from dataclasses import dataclass
from px_python_shared import (
    get_well_known_by_identifier,
    get_well_known,
    make_bearer_headers,
    add_scheme_from_auth_host,
)

log = logging.getLogger(__name__)


@dataclass
class IotDeviceExistsResponse:
    """Response for iot_device_exists"""

    exists: bool
    remember_device: bool = False
    id: str = None


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
    is_loaded: bool

    auth_host: Union[None, str]
    app_host: Union[None, str]
    identifier: Union[None, str]
    device_id: Union[None, str]

    well_known: Union[None, dict]
    access_token: Union[None, str]
    access_token_expires_at: Union[None, int]

    def __init__(self) -> None:
        self.is_loaded = False

        self.auth_host = None
        self.app_host = None
        self.identifier = None
        self.device_id = None

        self.well_known = None
        self.access_token = None
        self.access_token_expires_at = None

    def load(self, identifier: Union[str, None] = None):
        from px_device_identity import is_superuser_or_quit

        is_superuser_or_quit()

        log.info("Loading API with identifier %s ...", identifier)

        self.identifier = identifier
        if identifier is None:
            log.warning("Well known identifier is undefined.")
        else:
            result = self.refresh_well_known()
            if result:
                self.is_loaded = True

    def renew_token(self):
        """Renew access token"""
        if self.app_host is None:
            log.warning("No app host set.")
            raise Exception("No app host set.")

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
        try:
            well_known_list = get_well_known(device)
            if "data" not in well_known_list:
                log.warning("No well known found. API Error.")
                return None

            well_known = get_well_known_by_identifier(
                well_known=well_known_list["data"], identifier=self.identifier
            )

            if well_known is None or "data" not in well_known:
                log.warning("No well known found for %s.", self.identifier)
                return None

            self.app_host = add_scheme_from_auth_host(
                well_known["data"].hostname, device.properties.host
            )
            return well_known
        except Exception as e:
            log.error("Error getting well known: %s", e)
            return None

    async def submit_iot_data(self, data: list):
        """Submit iot data to server"""
        self.renew_token()

        log.debug("Submitting iot data %s", data)

        url = f"{self.app_host}/api/iot-devices/data/submit"
        res = requests.post(
            url,
            json={"data": data},
            headers=make_bearer_headers(self.access_token),
            timeout=5,
        )
        res.raise_for_status()

    def iot_device_exists(self, address: str):
        """Check if iot device exists"""
        self.renew_token()

        log.debug("Checking if iot device exists %s", address)

        url = f"{self.app_host}/api/iot-devices/exists"
        res = requests.post(
            url,
            json={"hardwareIdentifier": address},
            headers=make_bearer_headers(self.access_token),
            timeout=5,
        )
        res.raise_for_status()
        data = res.json()

        exists = "exists" in data and data["exists"] == True
        remember = "rememberDevice" in data and data["rememberDevice"] == True

        if exists and remember:
            # allowMultipleDeviceRelationships=true
            return IotDeviceExistsResponse(
                exists=data["exists"],
                remember_device=data["rememberDevice"],
                id=data["id"],
            )
        elif exists:
            # allowMultipleDeviceRelationships=false
            return IotDeviceExistsResponse(exists=data["exists"], remember_device=False)
        else:
            return IotDeviceExistsResponse(exists=False, remember_device=False)

    def create_iot_device(self, address: str):
        """Create iot device"""
        self.renew_token()

        log.info("Creating iot device %s", address)

        url = f"{self.app_host}/api/iot-devices"
        data = {
            "hardwareIdentifier": address,
            "model": "generic",
            "connectionType": "bluetooth_le",
            "connectionMeta": {},
            "supportedDataTypes": [],
        }
        res = requests.post(
            url, json=data, headers=make_bearer_headers(self.access_token), timeout=5
        )
        res.raise_for_status()
        data = res.json()

        return IotDeviceCreateResponse(
            hardwareIdentifier=data["hardwareIdentifier"],
            model=data["model"],
            connectionType=data["connectionType"],
            connectionMeta=data["connectionMeta"],
            supportedDataTypes=data["supportedDataTypes"],
            id=data["id"],
            createdAt=data["createdAt"],
            modifiedAt=data["modifiedAt"],
            revision=data["revision"],
        )

    def create_iot_device_if_not_exists(self, address: str):
        """Create iot device if not exists"""
        exists = self.iot_device_exists(address)

        log.debug("Iot device exists %s ...", exists)

        if exists.exists:
            return exists
        else:
            return self.create_iot_device(address)

    async def last_iot_device_data_submission(self, iot_device_id: str) -> int:
        """Get last iot device data submission timestamp"""
        self.renew_token()

        url = f"{self.app_host}/api/iot-devices/{iot_device_id}/last-data-submission"
        res = requests.get(
            url, headers=make_bearer_headers(self.access_token), timeout=5
        )
        return res.json()
