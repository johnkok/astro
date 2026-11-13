# Raspberry Pi astrophotography mount stack

This repository is the reproducible source of truth for the custom Servo42D
equatorial mount used with PINS/N.I.N.A., INDI, and PHD2 on Raspberry Pi.
It contains the Python ASCOM Alpaca driver, the timed-guide extension to INDI's
Alpaca telescope bridge, system services, sanitized application configuration,
and scripts for installing or validating a replacement Pi.

The reference system is a 64-bit Raspberry Pi running Debian 13 (trixie). Its
control path is:

```text
PINS/N.I.N.A. or PHD2
        |
        +-- INDI server :7624 -- indi_alpaca_telescope --+
        |                                                |
        +---------------- ASCOM Alpaca :11111 <----------+
                                     |
                              Servo42D driver
                                     |
                            SocketCAN can0 @ 500 kbit/s
                                     |
                         RA motor ID 2 / DEC motor ID 1
```

## Repository layout

- `drivers/servo42d-alpaca/` — complete Python Alpaca server source and tests.
- `drivers/indi-alpaca-telescope/` — the two modified INDI v2.2.5 source files.
- `rpi/` — systemd, SocketCAN, APT, INDI, and PINS configuration.
- `scripts/` — install, build, profile configuration, backup, and verification.
- `docs/` — architecture, deployment notes, source provenance, and Pi history.
- `3D/` — mechanical mount models already maintained in this repository.

Generated virtual environments, compiler output, logs, N.I.N.A. databases, and
full private profiles are intentionally excluded.

## New Pi quick start

Use a Raspberry Pi OS/Debian 13 arm64 image and create the `pi` user. Clone this
repository on the new Pi, review the hardware values in
`drivers/servo42d-alpaca/config.json` and `rpi/boot/config.txt.snippet`, then run:

```bash
cd astro
sudo ./scripts/install-rpi.sh
sudo reboot
./scripts/verify-rpi.sh
```

The installer adds the public Touch-N-Stars/PINS APT repository, installs PINS,
PHD2 and INDI, installs the Alpaca driver under `/opt`, builds the customized
INDI bridge from the pinned v2.2.5 source, configures CAN, restores the
non-private INDI/PINS files, and enables boot services.

After PINS/N.I.N.A. has created a profile, patch only its mount settings:

```bash
./scripts/configure-nina-profile.py \
  ~/.local/share/NINA/Profiles/YOUR-PROFILE.profile

./scripts/configure-phd2-profile.py ~/.PHDGuidingV2 --profile 2
```

The scripts create timestamped backups before changing profiles. Observatory
coordinates, camera serial numbers, credentials, sequences, and calibration
data remain local to each device.

## Development

Run the Alpaca driver without motors by changing `can.interface` to `virtual`
in a local config, then:

```bash
cd drivers/servo42d-alpaca
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest
```

To rebuild only the customized INDI driver:

```bash
sudo ./scripts/build-indi-driver.sh
```

See `docs/REPRODUCE.md` before deploying to hardware. This prototype has no
limit-switch, collision-avoidance, homing, or meridian-flip safety layer.

