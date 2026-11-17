# IM72D128V01XTMA1 MEMS microphone breakout

This KiCad project provides a small, simple breakout PCB for the IM72D128V01XTMA1 digital MEMS microphone.

## Included in the design

- Sensor footprint centered on the board
- 100 nF decoupling capacitor on VDD
- 10 kΩ pull-up to VDD on the SEL pin
- 5-pin header to expose VDD, GND, CLK, DATA, and SEL
- Compact 60 x 50 mm board outline for easy prototyping

## Notes

This is a practical reference board intended to be opened and adjusted in KiCad. The exact mechanical and pinout details should be confirmed against the manufacturer's latest datasheet before ordering bare boards or building a production design.

## Files

- `im72d128v01xtma1.kicad_pro` – KiCad project
- `im72d128v01xtma1.kicad_sch` – schematic
- `im72d128v01xtma1.kicad_pcb` – PCB layout

## Example signal map

- VDD: microphone supply rail
- GND: analog/digital ground
- CLK: digital clock output or input depending on interface
- DATA: digital audio data line
- SEL: mode select / left-right / configuration pin (verify against final datasheet)

The board is meant as a starting point for a digital MEMS audio interface, not as a final production release.
