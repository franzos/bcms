import argparse


def parse_cli_params():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Bluetooth Client Manager Service Python companion script to fetch data from bluetooth device and write to file."
    )

    # add argument
    parser.add_argument(
        "-t",
        "--test",
        type=bool,
        default=False,
        help="Simulate and write some test data",
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        default="default",
        help="Trigger notification for specific username",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        default=10,
        help="Sleep time in seconds between checks",
    )
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

    operation_args = {
        "run_test": False,
        "username": None,
        "sleep": 10,  # seconds
        "debug": False,
    }

    if args.test:
        operation_args["run_test"] = True

    if args.username is not None:
        operation_args["username"] = args.username

    if args.sleep is not None:
        operation_args["sleep"] = args.sleep

    if args.use_device_identity:
        operation_args["use_device_identity"] = True

    if args.application_identifier:
        operation_args["application_identifier"] = args.application_identifier

    if args.debug:
        operation_args["debug"] = True

    return operation_args
