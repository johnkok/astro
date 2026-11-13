# Architecture

## Components

### PINS/N.I.N.A.

PINS packages a Linux build of N.I.N.A. and manages the local INDI equipment
server. The selected telescope is the INDI device named `Alpaca Telescope`.
PINS/N.I.N.A. also exposes the selected telescope through its own Alpaca proxy
on `127.0.0.1:32330`; the boot connection helper connects that proxy after the
underlying INDI device is ready.

### INDI bridge

`indi_alpaca_telescope` translates INDI telescope properties to ASCOM Alpaca.
The repository's v2.2.5 modification adds the INDI timed guide vectors and maps
them to Alpaca `pulseguide`. Building against the same INDI release as the
installed libraries avoids the ABI mismatch seen with a newer master build.

### Servo42D Alpaca server

The Python service listens on TCP port 11111 and supports Alpaca UDP discovery
on port 32227. It owns the physical CAN connection and leases it per Alpaca
client so one application's disconnect does not interrupt other clients.

The driver maps RA to CAN node 2 and DEC to node 1. Both axes use a total ratio
of 864 motor revolutions per axis revolution and 16 microsteps. Acceleration is
180, the manual axis limit is 2 deg/s, and goto uses 1 deg/s.

Pulse guiding uses exact relative encoder displacement. This avoids rounding
small guide rates to an unusable integer motor RPM and restores tracking after
the guide interval.

### CAN

The reference Pi uses an MCP2515 on SPI, a 12 MHz oscillator, interrupt GPIO 25,
and SocketCAN interface `can0` at 500 kbit/s. `systemd-networkd` brings up the
interface and uses a 100 ms bus restart interval.

## Ports

| Port | Protocol | Owner | Purpose |
|---:|---|---|---|
| 7624 | TCP | INDI server | INDI clients and dynamically started drivers |
| 11111 | TCP | Servo42D Alpaca | Alpaca Telescope API |
| 32227 | UDP | Alpaca discovery | Network device discovery |
| 32330 | TCP | PINS/N.I.N.A. | Selected-equipment Alpaca proxy |
| 4400 | TCP | PHD2 | PHD2 event/control server |

## Boot ordering

1. `pins.service` starts PINS/N.I.N.A. and its INDI server.
2. `servo42d-alpaca.service` starts the physical mount driver.
3. `indi-alpaca-connect.service` waits for both, sets the bridge endpoint to
   `127.0.0.1:11111`, connects the INDI device, then connects the PINS proxy.

