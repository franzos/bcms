import argparse
from .config import (
    BLUETOOTH_SCAN_INTERVAL,
    DATA_SUBMISSION_INTERVAL,
)


def parse_cli_params():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Bluetooth Client Manager Service Python companion script to fetch data from bluetooth device and write to file."
    )

    # add argument
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        default="default",
        help="Trigger notification for specific username",
    )
    parser.add_argument(
        "-n",
        "--notify",
        type=bool,
        default=False,
        help="Trigger notification",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        default=BLUETOOTH_SCAN_INTERVAL,
        help="Sleep time in seconds between checks",
    )
    parser.add_argument(
        "-sd",
        "--sleep-data",
        type=int,
        default=DATA_SUBMISSION_INTERVAL,
        help="Sleep time in seconds between API submission",
    )
    # TODO: Deprecated
    parser.add_argument(
        "-di",
        "--use_device_identity",
        type=bool,
        default=False,
        help="Use device identity for authentication",
    )
    parser.add_argument(
        "-appid",
        "--application_identifier",
        type=str,
        default=None,
        help="Identify remote server to register ble devices with and log to. To be used with --use_device_identity",
    )
    parser.add_argument(
        "-d",
        "--debug",
        type=bool,
        default=False,
        help="Display more verbose debug logs",
    )

    # parse the arguments from standard input
    args = parser.parse_args()

    return {
        "username": args.username,
        "notify": args.notify,
        "sleep": args.sleep,
        "sleep_data": args.sleep_data,
        "use_device_identity": args.use_device_identity,
        "application_identifier": args.application_identifier,
        "debug": args.debug,
    }
