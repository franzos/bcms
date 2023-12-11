# Bluetooth Client Manager Service

## Features

- Track, Pair, Unpair devices
- Collect BLE data (passive & active)
- Submit data to API

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