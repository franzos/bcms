import asyncio
import capnp
import logging

from .bootstrap import (
    approve_device,
    devices_mem,
    list_devices,
    remove_device,
    async_queue,
)
from .devices_classes import BCMSDeviceInfo
from .config import pimstore_capnp, device_capnp, working_mode_capnp
from .queue import make_pair_request, make_unpair_request


log = logging.getLogger(__name__)


def make_device_info(device: BCMSDeviceInfo):
    device_info = device_capnp.new_message(
        address=device.address.__str__(),
        name=device.name.__str__(),
        approved=device.approved,
        paired=device.paired,
    )
    return device_info


def make_working_mode():
    working_mode = working_mode_capnp.new_message("approved")
    return working_mode


class RPCDeviceManager(pimstore_capnp.BCMS.Server):
    def list(self, onlyApproved: bool, _context, **kwargs):
        log.debug("Request list: %s", onlyApproved)
        devices = []

        known_devices = list_devices(max_age_s=60, only_approved=onlyApproved)
        for device in known_devices:
            capnp_device = make_device_info(device)
            devices.append(capnp_device)

        return devices, []

    def approve(self, address: str, _context, **kwargs):
        log.debug("Request approve: %s", address)
        try:
            success = approve_device(address)
            return success, []
        except Exception as err:
            return False, [str(err)]

    def remove(self, address: str, _context, **kwargs):
        log.debug("Request remove: %s", address)
        try:
            success = remove_device(address)
            return success, []
        except Exception as err:
            return False, [str(err)]

    def mode(self, _context, **kwargs):
        log.debug("Request mode")
        mode = make_working_mode()
        return mode

    def setMode(self, mode, _context, **kwargs):
        log.debug("Request setMode: %s", mode)
        return True

    def pair(self, address: str, _context, **kwargs):
        log.debug("Request pair: %s", address)
        async_queue.from_class(make_pair_request(address))
        return True, []

    def unpair(self, address: str, _context, **kwargs):
        log.debug("Request unpair: %s", address)
        async_queue.from_class(make_unpair_request(address))
        return True, []

    def isPaired(self, address: str, _context, **kwargs):
        log.debug("Request isPaired: %s", address)
        device = devices_mem.get(address)
        if device:
            return device.paired, []
        return False, []


class Server:
    async def myreader(self):
        while self.retry:
            try:
                # Must be a wait_for so we don't block on read()
                data = await asyncio.wait_for(self.reader.read(4096), timeout=0.5)
            except asyncio.TimeoutError:
                log.debug("  - reader timeout.")
                continue
            except Exception as err:
                log.warning("  - unknown myreader err: %s", err)
                return False
            await self.server.write(data)
        log.debug("  - reader done.")
        return True

    async def mywriter(self):
        while self.retry:
            try:
                # Must be a wait_for so we don't block on read()
                data = await asyncio.wait_for(self.server.read(4096), timeout=0.5)
                self.writer.write(data.tobytes())
            except asyncio.TimeoutError:
                log.debug("  - writer timeout.")
                continue
            except Exception as err:
                log.debug("  - unknown mywriter err: %s", err)
                return False
        log.debug("  - writer done.")
        return True

    async def myserver(self, reader, writer):
        # Start TwoPartyServer using TwoWayPipe (only requires bootstrap)
        self.server = capnp.TwoPartyServer(bootstrap=RPCDeviceManager())
        self.reader = reader
        self.writer = writer
        self.retry = True

        # Assemble reader and writer tasks, run in the background
        coroutines = [self.myreader(), self.mywriter()]
        tasks = asyncio.gather(*coroutines, return_exceptions=True)

        while True:
            self.server.poll_once()
            # Check to see if reader has been sent an eof (disconnect)
            if self.reader.at_eof():
                self.retry = False
                break
            await asyncio.sleep(0.01)

        # Make wait for reader/writer to finish (prevent possible resource leaks)
        await tasks


async def new_rpc_connection(reader, writer):
    server = Server()
    await server.myserver(reader, writer)
