# Reproducing the reference Raspberry Pi

## Before installation

- Use a 64-bit Raspberry Pi 5-compatible Debian 13/trixie image.
- Create a normal user named `pi`, or pass `--user NAME` to the installer.
- Confirm the CAN controller oscillator and interrupt GPIO. The committed
  defaults (`12 MHz`, GPIO `25`) are hardware-specific.
- Leave the motors mechanically disconnected for initial direction testing.
- Back up any existing PINS, N.I.N.A., PHD2, INDI, and `/opt` configuration.

## Install

```bash
git clone YOUR_REPOSITORY_URL astro
cd astro
sudo ./scripts/install-rpi.sh
sudo reboot
```

Useful installer options:

```text
--user NAME                 service account (default: pi)
--skip-pins                 do not install PINS/PHD2 packages
--skip-can                  do not edit boot/CAN configuration
--skip-indi-build           retain the distribution INDI bridge
--force-config              replace an existing Alpaca config after backup
--can-oscillator HZ         MCP2515 oscillator (default: 12000000)
--can-interrupt GPIO        MCP2515 interrupt GPIO (default: 25)
```

The installer is intended to be rerunnable. Before overwriting a managed file,
it saves a timestamped copy under `/var/backups/astro-stack/`.

## Configure application profiles

Start PINS/N.I.N.A. once so it creates a profile. Stop PINS before editing it:

```bash
sudo systemctl stop pins.service
./scripts/configure-nina-profile.py \
  ~/.local/share/NINA/Profiles/YOUR-PROFILE.profile
sudo systemctl start pins.service
```

For PHD2, create/select the intended equipment profile once, close PHD2, then:

```bash
./scripts/configure-phd2-profile.py ~/.PHDGuidingV2 --profile 2
```

Camera selection, USB identifiers, guiding calibration, observatory location,
and private notification/API settings must be configured on the new device.

## Verify

```bash
./scripts/verify-rpi.sh
```

Then perform these physical checks at a low speed:

1. Confirm `can0` is up and both motors answer.
2. Confirm RA and DEC move the expected physical axes.
3. Confirm positive/negative directions before attaching the drive train.
4. Test emergency stop and power removal.
5. Sync on a known position after every driver restart; the coordinate origin is
   not persistent.
6. Test PHD2 manual guide pulses while tracking.

## Updating from the reference Pi

Run `scripts/export-from-pi.sh pi@HOST` from a trusted development workstation.
It exports only the allow-listed source and non-private configuration. Review
`git diff`, run the tests, and update `docs/PI_CHANGE_HISTORY.md` before commit.

