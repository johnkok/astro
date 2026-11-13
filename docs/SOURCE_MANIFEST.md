# Source and configuration manifest

Export date: 2026-11-13 (Europe/Athens)  
Reference host: `pi@192.168.1.44`  
Reference OS: Debian 13.7 (trixie), aarch64

## Copied source

- `/opt/servo42d-ascom-alpaca/{src,tests,pyproject.toml,README.md}` to
  `drivers/servo42d-alpaca/`.
- `/home/pi/Projects/indi-v225-guide-fix/drivers/telescope/` customized
  `indi_alpaca_telescope.cpp` and `.h` to
  `drivers/indi-alpaca-telescope/`.

The rejected newer-INDI build, compiler output, virtual environments, Python
bytecode, pytest cache, pre-change snapshots, and installed binaries were not
copied. Git tracks maintainable source, not machine-specific artifacts.

## Copied configuration

- systemd units for PINS, Servo42D Alpaca, and automatic INDI connection.
- `/usr/local/bin/indi-alpaca-connect`.
- INDI `Alpaca Telescope_config.xml`.
- PINS/INDI `3rdparty.json` device registry.
- PINS APT source and its public signing key.
- SocketCAN `80-can.network` and the relevant boot overlay as a snippet.
- The working Servo42D hardware configuration.

## Deliberately sanitized or omitted

- The full N.I.N.A. profile was not exported. It contains observatory location,
  notification credential fields, paths, and unrelated equipment settings.
  `configure-nina-profile.py` applies only the seven required mount fields.
- The live PHD2 file was not exported. It includes camera identifiers,
  calibration, UI state, and unrelated guiding settings. A mount-only example
  and a profile patcher are provided.
- `NINA.sqlite`, logs, image data, sequences, dark libraries, and PHD2 debug or
  guide logs are not stored.
- PINS/N.I.N.A. application binaries are installed from the signed package
  repository rather than copied from `/home/pi/pins`.

## Current hardware values

| Setting | Value |
|---|---:|
| Alpaca endpoint | `127.0.0.1:11111`, device 0 |
| CAN interface | `can0`, 500000 bit/s |
| RA CAN node | 2 |
| DEC CAN node | 1 |
| RA/DEC gear ratio | 864 |
| Microsteps | 16 |
| Acceleration | 180 |
| Maximum manual axis rate | 2 deg/s |
| Goto rate | 1 deg/s |

