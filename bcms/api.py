import logging
from typing import Union
from dataclasses import dataclass
from px_python_shared.well_known import ApplicationsWellKnown
import requests

from px_python_shared import (
    get_well_known_by_identifier,
    make_bearer_headers,
    add_scheme_from_auth_host,
)

from bcms.config import HTTP_TIMEOUT_SECONDS

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
    auth_host: Union[None, str]
    app_host: Union[None, str]
    identifier: Union[None, str]

    well_known: Union[None, dict]

    def __init__(self, identifier: Union[str, None]) -> None:
        self.auth_host = None
        self.app_host = None
        # no identifier: offline use
        self.identifier = identifier
        if identifier is None:
            log.warning("Well known identifier is undefined.")
        else:
            log.info("Loading API with identifier %s ...", identifier)

        self.well_known = None
            
    def ready_api(self) -> None:
        """Check if identifier is set and refresh well known if necessary"""
        from px_device_identity import is_superuser_or_quit
        is_superuser_or_quit()
        
        if not self.identifier:
            raise ValueError("Well known identifier is not set")
        
        if self.well_known is None:
            self.refresh_well_known()
    
    def access_token_and_host(self) -> tuple:
        """Get access token and host"""
        from px_device_identity import Device

        device = Device()
        if not device.is_initiated:
            raise ValueError("Device is not initiated: Has it been registered yet?")
        
        result = device.get_access_token()

        return result["access_token"], device.properties.host

    def access_token(self) -> str:
        """Get access token"""
        access_token, idp_host = self.access_token_and_host()

        return access_token

    def refresh_well_known(self) -> ApplicationsWellKnown:
        """Refresh well known"""
        access_token, idp_host = self.access_token_and_host()
        
        self.well_known = get_well_known_by_identifier(
            idp_host, access_token, self.identifier
        )
        
        self.app_host = add_scheme_from_auth_host(
            self.well_known.hostname, idp_host
        )
        
        return self.well_known

    async def submit_iot_data(self, data: list):
        """Submit iot data to server"""
        log.debug("Submitting iot data %s", data)
        self.ready_api()

        url = f"{self.app_host}/api/iot-devices/data/submit"
        res = requests.post(
            url,
            json={"data": data},
            headers=make_bearer_headers(self.access_token()),
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        res.raise_for_status()

    def submit_iot_data_sync(self, data: list):
        """Submit iot data to server"""
        log.debug("Submitting iot data %s", data)
        self.ready_api()

        url = f"{self.app_host}/api/iot-devices/data/submit"
        res = requests.post(
            url,
            json={"data": data},
            headers=make_bearer_headers(self.access_token()),
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        res.raise_for_status()

    def iot_device_exists(self, address: str):
        """Check if iot device exists"""
        log.debug("Checking if iot device exists %s", address)
        self.ready_api()

        url = f"{self.app_host}/api/iot-devices/exists"
        res = requests.post(
            url,
            json={"hardwareIdentifier": address},
            headers=make_bearer_headers(self.access_token()),
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        data = res.json()

        exists = "exists" in data and data["exists"] is True
        remember = "rememberDevice" in data and data["rememberDevice"] is True

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

    def create_iot_device(
        self,
        hardware_identifier: str,
        model: str = "generic",
        connection_type: str = "bluetooth_le",
        connection_meta: Union[dict, None] = None,
        supported_data_types: Union[list, None] = None,
    ):
        """Create iot device"""
        log.info("Creating iot device %s", hardware_identifier)
        self.ready_api()

        url = f"{self.app_host}/api/iot-devices"
        data = {
            "hardwareIdentifier": hardware_identifier,
            "model": model,
            "connectionType": connection_type,
            "connectionMeta": connection_meta or {},
            "supportedDataTypes": supported_data_types or [],
        }
        
        log.info("Creating iot device with data %s", data)
        
        res = requests.post(
            url,
            json=data,
            headers=make_bearer_headers(self.access_token()),
            timeout=HTTP_TIMEOUT_SECONDS,
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
        self.ready_api()

        if exists.exists:
            return exists
        else:
            return self.create_iot_device(address)

    async def last_iot_device_data_submission(self, iot_device_id: str) -> int:
        """Get last iot device data submission timestamp"""
        self.ready_api()

        url = f"{self.app_host}/api/iot-devices/{iot_device_id}/last-data-submission"
        res = requests.get(
            url,
            headers=make_bearer_headers(self.access_token()),
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        # returns { timestamp: int, createdAt: Date }
        data = res.json()
        
        return data["timestamp"]
