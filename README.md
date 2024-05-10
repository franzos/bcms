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
- `--notify`: Display notifications
- `--username USERNAME`: username for notifications
- `--sleep`: sleep time between scans
- `--sleep-data`: sleep time between data submissions
- `--use_device_identity`: use device identity for authentication (and submit data to API)
- `--application_identifier`: identify remote server to register ble devices with and log to. To be used with --use_device_identity

To pair devices with PIN-prompt, running this in the background can be useful.:

```bash
bt-agent --capability=NoInputNoOutput
```

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

### Daemon CLI

Run the daemon CLI:

```bash
$ bcms-daemon --help
usage: bcms-daemon [-h] [-u USERNAME] [-n NOTIFY] [-s SLEEP] [-sd SLEEP_DATA] [-di USE_DEVICE_IDENTITY]
                   [-appid APPLICATION_IDENTIFIER] [-d DEBUG]

Bluetooth Client Manager Service Python companion script to fetch data from bluetooth device and write to file.

options:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Trigger notification for specific username
  -n NOTIFY, --notify NOTIFY
                        Trigger notification
  -s SLEEP, --sleep SLEEP
                        Sleep time in seconds between checks
  -sd SLEEP_DATA, --sleep-data SLEEP_DATA
                        Sleep time in seconds between API submission
  -appid APPLICATION_IDENTIFIER, --application_identifier APPLICATION_IDENTIFIER
                        Identify remote server to register ble devices with and log to.
  -d DEBUG, --debug DEBUG
                        Display more verbose debug logs
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