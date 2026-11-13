# Servo42D ASCOM Alpaca equatorial mount

An ASCOM Alpaca Telescope API for a two-axis equatorial mount using one MKS
SERVO42D/57D CAN controller for RA and one for DEC. Alpaca is discoverable by
ASCOM Platform on Windows and can be exposed to classic ASCOM/COM applications
through the ASCOM Device Hub / dynamic Alpaca driver.

## Implemented

- Separate RA and DEC CAN IDs, gear ratios, and direction reversal
- MKS commands: encoder-with-carry `0x30`, relative-axis position `0xF4`,
  speed `0xF6`, emergency stop `0xF7`, and the official additive checksum
- Connect, coordinates, Sync, synchronous GoTo, sidereal RA tracking,
  `MoveAxis` on both axes, four-direction `PulseGuide`, and AbortSlew
- Alpaca UDP discovery on port 32227 and management endpoints
- Virtual motors for development without hardware

## Important limitations

This is an engineering prototype, not yet safe for unattended operation. It
does **not** implement homing, limit switches, pier-side modelling, meridian
flips, collision avoidance, parking, PEC, refraction, or persistent alignment.
The coordinate origin is lost at restart and must be restored with Sync. Add
hardwired limit switches and test AbortSlew before coupling the motors.

GoTo currently uses the shortest RA path and does not choose or change the
German-equatorial pier side. The MKS `F4` command is signed 24-bit; configure
gear ratios so a full required move remains inside that range.

MKS speed units are integer motor RPM at 16/32/64 microsteps and scale at other
microstep values. Sidereal tracking is only accurate if the requested motor
RPM can be represented after rounding. For a 144:1 worm the target is about
0.1003 motor RPM, so continuous `F6` tracking cannot be accurate at 16
microsteps. Use sufficient total reduction and validate the actual shaft rate,
or add a firmware velocity layer that accepts fractional RPM.

## Hardware

- Two MKS SERVO42D_CAN or SERVO57D_CAN boards with different node IDs
- A supported CAN adapter (SocketCAN on Linux/Raspberry Pi is the default
  hardware example; `python-can` also supports several Windows adapters)
- 120-ohm termination at both physical ends of the CAN bus
- Common CAN ground and a suitable motor power supply

The ASCOM server may run on the Raspberry Pi next to the mount; Windows imaging
software discovers it over the LAN.

## Install and run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
cp config.example.json config.json
servo42d-alpaca --config config.json
```

The example selects `socketcan/can0` at 500 kbit/s with RA node 1 and DEC node
2. To test without motors, set `can.interface` to `virtual` and choose any
channel name. On Linux, configure SocketCAN before starting, for example:

```bash
sudo ip link set can0 up type can bitrate 500000
```

Open `http://HOST:11111/docs` for the generated API console. In Windows ASCOM
Device Hub, discover Alpaca devices on the same subnet and select
`Servo42D Equatorial Mount`.

## Configuration that must match the mechanics

`ra_gear_ratio` and `dec_gear_ratio` are motor revolutions per axis revolution,
including every belt and gearbox stage. `*_positive_direction` defines which
physical direction increases the corresponding sky coordinate. Start with the
motors mechanically disconnected, use a very low axis rate, and verify both
signs before attachment.

## Tests

```bash
pytest
```

The tests validate MKS framing/checksum, dual-axis coordinate conversion and
GoTo in the simulator, and core Alpaca responses.
