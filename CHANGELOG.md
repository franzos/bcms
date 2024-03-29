# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)

## [0.0.7]

### Changed

- Notifications default to `False`

## [0.0.6]

### Changed

- Added switch to disable notifications
- Made timeout for scanning and submission configurable

## [0.0.5]

### Changed

- Moved some stuff to shared library `px-python-shared`

## [0.0.4]

### Changed

- Better handling when running with `--use_device_identity` before registering

## [0.0.3]

### Changed

- IOT data check and submission async
- Scan for 5s (down from 10s) for faster response
- Clear old data every 180s, older than 180s
- Submit data every 30s
- Revision of BLE data retrieval

### Fixed

- Made unpairing more robust, in case 2nd try is needed

## [0.0.2]

### Fixed

- CI script

## [0.0.1]

### Changed

- Initial release
