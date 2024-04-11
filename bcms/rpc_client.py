import argparse
import capnp
import asyncio
import socket

from .utils import format_boolean
from .config import RPC_ADDRESS, RPC_PORT, pimstore_capnp


async def myreader(client, reader):
    while True:
        data = await reader.read(4096)
        client.write(data)


async def mywriter(client, writer):
    while True:
        data = await client.read(4096)
        writer.write(data.tobytes())
        await writer.drain()


class BCMSClientConnection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.client = capnp.TwoPartyClient()
        self.coroutines = [myreader(self.client, reader), mywriter(self.client, writer)]
        asyncio.gather(*self.coroutines, return_exceptions=True)

    def get_bcms(self):
        return self.client.bootstrap().cast_as(pimstore_capnp.BCMS)


class BCMSClient:
    def __init__(self, client_connection: BCMSClientConnection):
        self.bcms = client_connection.get_bcms()

    def list(self, only_approved):
        return self.bcms.list(onlyApproved=only_approved).a_wait()

    def approve(self, address):
        return self.bcms.approve(address=address).a_wait()

    def remove(self, address):
        return self.bcms.remove(address=address).a_wait()

    def mode(self):
        return self.bcms.mode().a_wait()

    def set_mode(self, mode):
        return self.bcms.setMode(mode=mode).a_wait()

    def pair(self, address):
        return self.bcms.pair(address=address).a_wait()

    def unpair(self, address):
        return self.bcms.unpair(address=address).a_wait()

    def is_paired(self, address):
        return self.bcms.isPaired(address=address).a_wait()


async def main_loop(args):
    reader, writer = await asyncio.open_connection(
        RPC_ADDRESS, RPC_PORT, family=socket.AF_INET
    )

    client = BCMSClient(BCMSClientConnection(reader, writer))

    if args.command == "list":
        result = await client.list(args.only_approved)
        # client.client.close()
        if result.errors and len(result.errors) > 0:
            print(f"Errors: {result.errors}")
            return

        for device in result.devices:
            print(
                f"- {device.address} | APPRO: {format_boolean(device.approved)} PAIRE: {format_boolean(device.paired)} | {device.name}"
            )

        print()
        print(
            f"Total: {len(result.devices)} devices, {len([d for d in result.devices if d.approved])} approved, {len([d for d in result.devices if d.paired])} paired."
        )
        print("Only devices seen in the last 30s are listed.")

    elif args.command == "mode":
        print(await client.mode())
    elif args.command == "set_mode":
        print(await client.set_mode(args.mode))
    else:
        if args.address is None:
            print(f"The {args.command} command requires the --address argument.")
            return

        if args.command == "approve":
            print(await client.approve(args.address))
        elif args.command == "remove":
            print(await client.remove(args.address))
        elif args.command == "pair":
            print(await client.pair(args.address))
            print(
                "You should receive a notification when (& if) the pairing was successful."
            )
        elif args.command == "unpair":
            print(await client.unpair(args.address))
            print(
                "You should receive a notification when (& if) the unpairing was successful."
            )
        elif args.command == "is_paired":
            print(await client.is_paired(args.address))

    return


def main():
    parser = argparse.ArgumentParser(description="BCMS Client")
    parser.add_argument(
        "command",
        choices=[
            "list",
            "approve",
            "remove",
            "mode",
            "set_mode",
            "pair",
            "unpair",
            "is_paired",
        ],
    )
    parser.add_argument("--address", default=None)
    parser.add_argument(
        "--only_approved", default=False, action=argparse.BooleanOptionalAction
    )
    parser.add_argument("--mode", default=None)

    args = parser.parse_args()

    asyncio.run(main_loop(args))


if __name__ == "__main__":
    main()
