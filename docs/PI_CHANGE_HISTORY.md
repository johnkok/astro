# Servo42D / Alpaca / INDI change history

Generated: 2026-10-26 (Europe/Athens)  
Host: `pi@192.168.1.44`

## Scope and audit limitation

This is a best-effort inventory of files created, modified, replaced, or deliberately touched during the Servo42D mount integration and troubleshooting work of 2026-10-24 through 2026-10-26. Linux does not keep a complete, authoritative record of which interactive session touched every file, and access times may be disabled or updated by reads. The list therefore separates intentional configuration/code changes from backups and automatically generated build/runtime artifacts.

The current control path is:

`N.I.N.A./PHD2/INDI -> 127.0.0.1:11111 -> servo42d-alpaca -> Servo42D motors`

The mount axis mapping is RA motor ID `2` and DEC motor ID `1`.

## Intentional persistent files

| Action | File | Description |
|---|---|---|
| Created | `/etc/systemd/system/servo42d-alpaca.service` | System service that starts the Alpaca server at boot from its Python virtual environment, using `/opt/servo42d-ascom-alpaca/config.json`, and restarts it after failures. The service is enabled. |
| Created | `/etc/systemd/system/indi-alpaca-connect.service` | Enabled boot-time one-shot service that waits for PINS and the Alpaca server, then restores the INDI/Alpaca connections. |
| Created/modified | `/usr/local/bin/indi-alpaca-connect` | Boot connection helper. Configures the INDI Alpaca Telescope for `127.0.0.1:11111`, connects it with retries, and connects the N.I.N.A. Alpaca proxy at `127.0.0.1:32330`. |
| Replaced | `/usr/bin/indi_alpaca_telescope` | Custom ABI-compatible build based on INDI v2.2.5. Adds INDI timed-guide properties (`TELESCOPE_TIMED_GUIDE_NS` and `TELESCOPE_TIMED_GUIDE_WE`) and maps north/south/east/west guide commands to Alpaca `pulseguide`. |
| Modified | `/opt/servo42d-ascom-alpaca/config.json` | Sets RA motor ID `2`, DEC motor ID `1`, both gear ratios to `864`, both directions to `ccw`, maximum axis rate to `2 deg/s`, goto rate to `1 deg/s`, and acceleration to `180` for smoother acceleration/braking (previously `236`). |
| Modified | `/opt/servo42d-ascom-alpaca/src/servo42d_ascom/api.py` | Completed missing Alpaca telescope API properties/endpoints used by N.I.N.A., including altitude and azimuth. Added per-client connection leases keyed by source address and Alpaca `ClientID`, preventing one client from disconnecting the physical mount while another client still uses it. |
| Modified | `/opt/servo42d-ascom-alpaca/src/servo42d_ascom/mount.py` | Added altitude/azimuth and site/time support. Reworked pulse guiding to use exact relative encoder moves rather than low, rounded RPM commands; added overlapping-guide timing/generation handling and correct tracking restoration. |
| Modified | `/opt/servo42d-ascom-alpaca/tests/test_driver.py` | Added coverage for required N.I.N.A. API behavior, client connection leases, axis capabilities, exact guide pulses, and tracking behavior during/after guide pulses. The resulting suite passed 8 tests. |
| Modified by setup/runtime | `/home/pi/Documents/INDI/3rdparty.json` | Registers `indi_alpaca_telescope` with label `Alpaca Telescope` and type `telescope`, making it selectable in the equipment UI. The application may rewrite this file during normal operation. |
| Created/modified | `/home/pi/.indi/Alpaca Telescope_config.xml` | Persistent INDI device settings: Alpaca address `127.0.0.1`, port `11111`, TCP transport, polling interval, tracking mode, and slew-rate settings. |
| Created/modified | `/home/pi/.indi/Alpaca Telescope_config.xml.default` | Default/saved copy of the same INDI Alpaca Telescope settings. |
| Modified by setup/runtime | `/home/pi/.local/share/NINA/Profiles/9a2cea8a-a5ac-4df1-ba60-96ec4c65cd23.profile` | N.I.N.A. profile `Ikok_test`. Selects `Alpaca Telescope` through INDI at `127.0.0.1:11111` using `indi_alpaca_telescope`; plugin storage also records direct Alpaca device 0 at the same endpoint. N.I.N.A. may rewrite this file. |
| Modified by setup/runtime | `/home/pi/.PHDGuidingV2` | PHD2 configuration. Profiles 1 and 2 contain Alpaca endpoint `127.0.0.1:11111:0`; profile 2 also identifies the INDI mount as `Alpaca Telescope`. PHD2 may rewrite this file. |
| Created | `/home/pi/SERVO42D_CHANGE_HISTORY.md` | This history and recovery inventory. |

## Safety backups and recovery copies

| File | Description |
|---|---|
| `/opt/servo42d-ascom-alpaca/config.json.bak-20261025-before-axis-map-fix` | Configuration before correcting the RA/DEC motor mapping. |
| `/opt/servo42d-ascom-alpaca/src/servo42d_ascom/api.py.pre-client-leases` | API implementation before per-client connection leasing. |
| `/opt/servo42d-ascom-alpaca/tests/test_driver.py.pre-client-leases` | Tests before connection-lease coverage. |
| `/opt/servo42d-ascom-alpaca/backups/20261024-before-alpaca-api-completion/src/servo42d_ascom/api.py` | API snapshot before completing the Alpaca endpoints required by clients. |
| `/opt/servo42d-ascom-alpaca/backups/20261024-before-alpaca-api-completion/src/servo42d_ascom/mount.py` | Mount implementation snapshot before API completion. |
| `/opt/servo42d-ascom-alpaca/backups/20261024-before-alpaca-api-completion/tests/test_driver.py` | Test snapshot before API completion. |
| `/opt/servo42d-ascom-alpaca/backups/20261025-before-guide-fixes/mount.py` | Mount implementation before pulse-guide fixes. |
| `/opt/servo42d-ascom-alpaca/backups/20261025-before-guide-fixes/test_driver.py` | Tests before pulse-guide fixes. |
| `/opt/servo42d-ascom-alpaca/backups/20261025-before-guide-fixes/indi_alpaca_telescope` | Previously installed INDI Alpaca Telescope executable. |
| `/opt/servo42d-ascom-alpaca/backups/20261025-before-smooth-ramp/config.json` | Configuration before reducing acceleration for smoother ramps. |
| `/home/pi/.PHDGuidingV2.pre-client-leases` | PHD2 configuration snapshot taken before the connection-lease change. |
| `/home/pi/.PHDGuidingV2.pre-localhost-match` | PHD2 configuration before standardizing the mount endpoint on localhost. It records the earlier `127.0.0.1:32330:0` proxy endpoint. |
| `/home/pi/.local/share/NINA/Profiles/9a2cea8a-a5ac-4df1-ba60-96ec4c65cd23.profile.pre-indi-fix` | N.I.N.A. profile before the INDI selection fix. |
| `/home/pi/.local/share/NINA/Profiles/9a2cea8a-a5ac-4df1-ba60-96ec4c65cd23.profile.pre-localhost-match` | N.I.N.A. profile before matching the localhost endpoint. |
| `/home/pi/.local/share/NINA/Profiles/9a2cea8a-a5ac-4df1-ba60-96ec4c65cd23.profile.bkp` | N.I.N.A.-generated profile backup. |

## INDI source and build worktrees

The following directories were created for building the guide-capable INDI driver. They contain many upstream source files and automatically generated compiler files, so their contents are grouped here instead of misleadingly presenting every checkout/build file as a hand edit.

| Path | Description |
|---|---|
| `/home/pi/Projects/indi-guide-fix/` | Detached worktree at commit `96f9e53` (then-current master). `drivers/telescope/indi_alpaca_telescope.cpp` and `.h` were modified for timed guiding; `build/` contains generated compiler output. Its resulting executable had an ABI mismatch and was not retained as the installed driver. |
| `/home/pi/Projects/indi-v225-guide-fix/` | Detached worktree at official INDI v2.2.5 commit `1dd9b34`. The same two telescope source files were modified, and `build/` contains generated compiler output. This worktree produced the executable currently installed at `/usr/bin/indi_alpaca_telescope`. |
| `/home/pi/Projects/indi/.git/` | Git metadata touched when fetching master and tag v2.2.5 and when registering the two worktrees, including `.git/worktrees/` entries. The main source checkout was not used as the installed custom binary. |

## Generated and runtime artifacts

These paths were created or updated as a consequence of installing, testing, building, or running the software. They are not primary hand-maintained configuration:

- `/opt/servo42d-ascom-alpaca/.venv/` — Python virtual environment and editable-install metadata.
- `/opt/servo42d-ascom-alpaca/.pytest_cache/` — pytest cache.
- `/opt/servo42d-ascom-alpaca/tests/__pycache__/` — compiled Python test bytecode.
- `/opt/servo42d-ascom-alpaca/src/servo42d_ascom/__pycache__/` — compiled Python driver bytecode, including updated `api` and `mount` modules.
- `/home/pi/Projects/indi-guide-fix/build/` — generated CMake/compiler files for the rejected master build.
- `/home/pi/Projects/indi-v225-guide-fix/build/` — generated CMake/compiler files for the installed v2.2.5 build.
- `/home/pi/Documents/PHD2/PHD2_GuideLog_2026-10-24_131157.txt`
- `/home/pi/Documents/PHD2/PHD2_DebugLog_2026-10-24_131157.txt`
- `/home/pi/Documents/PHD2/PHD2_GuideLog_2026-10-25_123830.txt`
- `/home/pi/Documents/PHD2/PHD2_DebugLog_2026-10-25_123830.txt`
- `/home/pi/phd2.1` — 5-byte PHD2 runtime/process-state file; this is not the mount configuration.
- systemd journal entries for `servo42d-alpaca.service` and `indi-alpaca-connect.service` — runtime logs held by journald rather than project files.

## Key-file SHA-256 fingerprints

These fingerprints identify the versions present when this history was prepared:

```text
aec051c1905991f7245548c53d71bf9c9c891bba567f7d032c91f857783c4e5e  /opt/servo42d-ascom-alpaca/config.json
9645cb01e8a268bb5875265e025ad7796769ea3cadbd3e214cc754f33893acfd  /opt/servo42d-ascom-alpaca/src/servo42d_ascom/api.py
a7685e65c2f94f2869a4ac7dd089a7796a38bf699daa4ac5b1e902ed5e44586d  /opt/servo42d-ascom-alpaca/src/servo42d_ascom/mount.py
799cd7b87d4e308e4d5c5ecf24e59599048dde81615531cbb027a2885b70e1a7  /opt/servo42d-ascom-alpaca/tests/test_driver.py
72254ecdfdd0b3e2d89fe11957efcfe07748fb8baf96e99b42f1018d14d053ac  /usr/bin/indi_alpaca_telescope
82ebba54b83f05b5a2f49129abc072369830f69e76e102c006300e296d06b62d  /etc/systemd/system/servo42d-alpaca.service
a82b506e0143d0e2218865a3537823803cbfd487611c2acf72aa41ed933e519d  /etc/systemd/system/indi-alpaca-connect.service
63bcd33fb209855fb8075e8a0d9462f01c4c4c52f428fda161f61c01b94ca9d  /usr/local/bin/indi-alpaca-connect
f226407531132c154d97eaef23cf40cd7c978c39331d1abb1c5dfb130cfa1348  /home/pi/Documents/INDI/3rdparty.json
```

## Operational result

- The Alpaca server is configured to start automatically at boot.
- INDI reconnects to the local Alpaca endpoint automatically after startup.
- N.I.N.A. and PHD2 use `127.0.0.1:11111` for the Servo42D mount.
- Multiple clients can remain connected without one client's disconnect shutting down the physical mount connection for the others.
- INDI/PHD2 timed guide commands reach the Alpaca pulse-guide implementation.
- Guide pulses use exact encoder displacement and resume the prior tracking state.
- Acceleration was reduced to make starting and braking smoother.

## 2026-11-13 — Development repository export

Created a reproducible development/deployment tree in the Git repository
`/home/johnkokko/Documents/GitHub/astro` on the development workstation.
No running Pi service, driver, motor configuration, PINS profile, or PHD2
profile was changed during the export.

Pi files read and exported as maintainable source or non-private configuration:

- `/opt/servo42d-ascom-alpaca/src/servo42d_ascom/*.py`
- `/opt/servo42d-ascom-alpaca/tests/test_driver.py`
- `/opt/servo42d-ascom-alpaca/{README.md,pyproject.toml,config.example.json,config.json}`
- `/home/pi/Projects/indi-v225-guide-fix/drivers/telescope/indi_alpaca_telescope.{cpp,h}`
- `/etc/systemd/system/{pins,servo42d-alpaca,indi-alpaca-connect}.service`
- `/usr/local/bin/indi-alpaca-connect`
- `/home/pi/.indi/Alpaca Telescope_config.xml`
- `/home/pi/Documents/INDI/3rdparty.json`
- `/etc/systemd/network/80-can.network`
- `/etc/apt/sources.list.d/pins.list`
- `/usr/share/keyrings/pins-archive-keyring.gpg` (public signing key)

The full live N.I.N.A. profile, PHD2 profile, databases, application binaries,
logs, virtual environments, build trees, and cache files were deliberately not
exported. The repository uses sanitized mount-only templates and patch scripts
so observatory coordinates, credentials, camera identifiers, and calibration
remain private to each device.

Repository support files created include architecture/reproduction/source
documentation; version and package manifests; PINS/CAN/systemd templates; and
scripts to install the stack, build the modified INDI driver, patch N.I.N.A. and
PHD2 mount settings, back up a Pi, export reviewed source, and verify services.

Verification performed:

- Servo42D test suite: `8 passed` on the reference Pi.
- All added shell scripts passed `bash -n`.
- Both profile configuration scripts passed Python compilation and functional
  fixture tests, including idempotent second runs and backup creation.
- Repository scan found no exported credentials, private profiles, databases,
  generated bytecode, virtual environments, or build output.
- This history file was updated at `/home/pi/SERVO42D_CHANGE_HISTORY.md` and its
  repository copy at `docs/PI_CHANGE_HISTORY.md`.
- The exported repository tree was reviewed and committed to the `main` branch
  as a single reproducible-stack change; pushing remains a separate operation.

