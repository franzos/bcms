# Development

```bash
guix shell -m manifest.scm
python3 -m venv venv
source venv/bin/activate
pip3 install --no-dependencies .
# Might be required for dbus
export PYTHONPATH=$(env | grep GUIX_PYTHONPATH | cut -d '=' -f 2 | cut -d ':' -f 1):$PYTHONPATH
bcms-daemon --debug True
```

One-liner client:

```bash
guix shell \
    -D bcms \
    -- python3 -m bcms.rpc_client list
```

One-liner daemon:

```bash
guix shell \
    -D bcms \
    -- python3 -m bcms.main
```

It's easy to manually make requests, based on the device keys; For ex.:

```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $(px-device-identity -o GET_ACCESS_TOKEN | jq -r .access_token)" -d '{"hardwareIdentifier":"abc"}' https://vhh-server.ones-now.com/api/iot-devices/exists
```

### Known Issues

The current, stable `pycapnp` package (`v1.3`) does not support async RPC calls; I'm using a queue until this is fixed, but this makes the RPC client a little less precise (e.g. it won't wait until your pairing request has succeeded before returning). This is suppored as of `v2.0.0b1`: [ref](https://github.com/capnproto/pycapnp/blob/master/CHANGELOG.md#v200b1-2023-10-03), but has not been released yet.

### Tests

Run all tests:

```bash
python -m unittest discover tests
```

Run a specific test:

```bash
python3 tests/test_rpc_client.py
```