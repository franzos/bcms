# Bluetooth Client Manager Service

## Features

- Track, Pair, Unpair devices
- Collect BLE data (passive & active)
- Submit data to API

Defaults:

 - Bluetooth scan for 5s
 - IOT API data submission every 30s
 - Clear IOT data cache every 180s
 - RPC port: `4567`

## Usage

### Daemon

Run the daemon:

```bash
bcms-daemon --debug True
```

All arguments:

- `--debug`: Enable debug logging
- `--username USERNAME`: username for notifications
- `--use_device_identity`: use device identity for authentication (and submit data to API)
- `--application_identifier`: identify remote server to register ble devices with and log to. To be used with --use_device_identity

### CLI

Run the CLI:

```bash
$ bcms --help
usage: bcms [-h] [--address ADDRESS] [--only_approved | --no-only_approved] [--mode MODE]
            {list,approve,remove,mode,set_mode,pair,unpair,is_paired}

BCMS Client

positional arguments:
  {list,approve,remove,mode,set_mode,pair,unpair,is_paired}

options:
  -h, --help            show this help message and exit
  --address ADDRESS
  --only_approved, --no-only_approved
  --mode MODE
```

For example, to list devices:

```bash
bcms list
```

To request pairing:

```bash
bcms pair --address 00:11:22:33:44:55
```

### RPC

The CLI relies on a RPC interface which you can use, too:

```
interface BCMS {
    list     @0 (onlyApproved :Bool) -> (devices :List(BCMSDeviceInfo), errors :List(Text));
    approve  @1 (address :Text) -> (status :Bool, errors :List(Text));
    remove   @2 (address :Text) -> (status :Bool, errors :List(Text));
    mode     @3 () -> (mode :BCMSWorkingMode);
    setMode  @4 (mode :BCMSWorkingMode) -> (status: Bool, errors :List(Text));
    pair     @5 (address :Text) -> (status :Bool, errors :List(Text));
    unpair   @6 (address :Text) -> (status :Bool, errors :List(Text));
    isPaired @7 (address :Text) -> (status :Bool, errors :List(Text));
}
```

Checkout `bcms/rpc/bcms.capnp` for more details.

## Spec

IOT data is submitted to the backend like so:

```json
{
    "data": [
        {
            "iotDeviceId": "cd553938-8960-4e70-864a-a7fba06578c0",
            "dataType": "heart_rate",
            "data": [
                {
                    "timestamp": "1642694304",
                    "data": {
                        "rate": "67"
                    }
                },
                {
                    "timestamp": "1642694364",
                    "data": {
                        "rate": "66"
                    }
                }
            ]
        },
        {
            "iotDeviceId": "cd553938-8960-4e70-864a-a7fba06578c0",
            "dataType": "battery_level",
            "data": [
                {
                    "timestamp": "1642694364",
                    "data": {
                        "level": "22"
                    }
                }
            ]
        }
    ]
}
```

## Development

```bash
export PYTHONPATH="/gnu/store/yknv27l3kzv1cv1zw3jzd00yczz5cqsb-python-dbus-1.2.18/lib/python3.10/site-packages:$PYTHONPATH"
bcms-daemon --debug True
```

## Known Issues

The current, stable `pycapnp` package (`v1.3`) does not support async RPC calls; I'm using a queue until this is fixed, but this makes the RPC client a little less precise (e.g. it won't wait until your pairing request has succeeded before returning).

This is suppored as of `v2.0.0b1`: [ref](https://github.com/capnproto/pycapnp/blob/master/CHANGELOG.md#v200b1-2023-10-03), but has not been released yet.

## Tests

Run all tests:

```bash
python -m unittest discover tests
```

Run a specific test:

```bash
python3 tests/test_rpc_client.py
```



rsync -av --exclude-from=.gitignore . softmax@10.10.10.233:/tmp/bcms

systemctl stop bluetooth-client-manager-python.service
systemctl stop bluetooth-client-manager.service

pip install . --break-system-packages


bcms-daemon --debug True --use_device_identity True --application_identifier vhh-server --username default




apt install bluez-tools
bt-agent --capability=NoInputNoOutput