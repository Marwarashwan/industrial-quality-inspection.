# EasyEDA wiring reference

Proposed control wiring for the inspection cell: a Raspberry Pi running the OpenPLC runtime, with start/stop buttons, an e-stop contact, a part sensor, three status LEDs and one relay that enables the robot. Use it to place parts and draw nets in EasyEDA.

Concept design, not built or tested. A software e-stop is not a safety function. A real machine needs a hardware safety circuit that cuts power to the robot.

## Before you draw

- Pi GPIO is 3.3 V only. Nothing on a GPIO net may ever see 5 V.
- The OpenPLC Raspberry Pi driver has its own fixed table that maps addresses like `%IX0.0` to GPIO pins. The GPIO column below is a sensible starting layout. Look up OpenPLC's table first and swap the GPIO and header pin columns to match before you route a board.
- The PLC addresses match the ladder variables you started. The new ones (`PART_PRESENT`, the LEDs) need adding to the PLC variable table later.

## Pin map

| Signal | PLC address | GPIO | Header pin | Direction | What it connects to |
| --- | --- | --- | --- | --- | --- |
| START_PB | %IX0.0 | 17 | 11 | Input | Start pushbutton, normally open |
| STOP_PB | %IX0.1 | 27 | 13 | Input | Stop pushbutton, normally open |
| ESTOP_OK | %IX0.2 | 22 | 15 | Input | E-stop contact, normally closed. Reads 1 when healthy |
| PART_PRESENT | %IX0.3 | 23 | 16 | Input | IR reflective sensor module output |
| RUN_CMD | %QX0.0 | 19 | 35 | Output | Relay driver, contact goes to the robot enable terminal |
| LED_GREEN | %QX0.1 | 5 | 29 | Output | Confident pass |
| LED_YELLOW | %QX0.2 | 6 | 31 | Output | Unsure, needs review |
| LED_RED | %QX0.3 | 13 | 33 | Output | Non-object or fault |

Power pins: 3V3 on header pin 1, 5 V on pin 2, ground on pin 6 (any ground pin works, but use one net called GND).

## Circuit blocks

### 1. Pushbutton input (START_PB, STOP_PB)

```
3V3 ──[ SW normally open ]──┬──[ 1 kΩ ]──► GPIO
                            └──[ 10 kΩ ]──► GND
```

Pressed reads high. The 10 kΩ pulls the pin low when released. The 1 kΩ protects the GPIO if the wiring is ever shorted.

### 2. E-stop input (ESTOP_OK)

```
3V3 ──[ E-STOP contact, normally closed, on a screw terminal ]──┬──[ 1 kΩ ]──► GPIO22
                                                                 └──[ 10 kΩ ]──► GND
```

Healthy reads high. Pressing the e-stop or breaking the wire reads low, so a cut cable fails safe. In the ladder, use `ESTOP_OK` as a normally open contact in the run rung (or invert it into your `ESTOP_ACTIVE` variable).

### 3. Part sensor (PART_PRESENT)

```
3-pin header for the IR module:   VCC ──► 3V3
                                  GND ──► GND
                                  OUT ──[ 1 kΩ ]──► GPIO23
```

Use a reflective IR module that runs on 3.3 V. Many of these modules pull OUT low when something is detected, so check yours and invert it in the ladder if needed. A 5 V sensor needs a level shifter or a resistor divider first.

### 4. Status LED (repeat three times)

```
GPIO ──[ 330 Ω ]──►|── GND
                  LED anode to cathode
```

Roughly 3 to 4 mA at 3.3 V, enough to see and safe for the pin. Use green, yellow and red.

### 5. Relay driver (RUN_CMD)

```
GPIO19 ──[ 1 kΩ ]──┬── base   NPN (2N2222 or S8050)
                    └──[ 10 kΩ ]── GND        keeps the relay off while the Pi boots

NPN emitter   ──► GND
NPN collector ──► relay coil pin B
relay coil pin A ──► +5 V
1N4007 across the coil: cathode to +5 V, anode to the collector

Relay COM and NO ──► 3-pin screw terminal "ROBOT_ENABLE"
```

The diode absorbs the voltage spike when the coil switches off. The robot only sees a dry contact, so it stays electrically separate from the Pi.

## Parts list

| Part | Qty | Search term in EasyEDA |
| --- | --- | --- |
| Raspberry Pi 40-pin socket | 1 | 2x20 female header 2.54 mm |
| Tactile pushbutton | 2 | tactile switch |
| Resistor 1 kΩ | 5 | 1k resistor 0603 or axial |
| Resistor 10 kΩ | 4 | 10k resistor |
| Resistor 330 Ω | 3 | 330 ohm resistor |
| LED green, yellow, red | 3 | LED 3 mm or 5 mm |
| NPN transistor | 1 | 2N2222 or S8050 |
| Diode | 1 | 1N4007 |
| 5 V relay | 1 | SRD-05VDC-SL-C |
| 2-pin screw terminal | 1 | screw terminal 2 pin 5.08 mm (e-stop contact) |
| 3-pin screw terminal | 1 | screw terminal 3 pin 5.08 mm (ROBOT_ENABLE) |
| 3-pin header | 1 | pin header 1x3 (IR module) |

The camera connects by USB or the Pi's camera ribbon, and the ring light runs from its own 5 V supply. Neither belongs on this schematic.

## Build order in EasyEDA

1. Create a project and a new schematic. Name it `inspection_cell_control`.
2. Place the 2x20 header first and label each pin you use with its signal name (`START_PB`, `STOP_PB` and so on) using net labels. Label pin 1 `3V3`, pin 2 `+5V` and pin 6 `GND`.
3. Draw one circuit block at a time from the sketches above, in the order of the pin map. Connect each block to the header by net label, not by long wires.
4. Use one `GND` net everywhere. The relay coil and the Pi must share ground.
5. Run the design rule check. Fix every unconnected pin and every net with a single connection.
6. Check each input net against the blocks above. Confirm no 5 V net touches a GPIO.
7. Only then convert to a PCB, if you want one. A breadboard or perfboard build from this schematic works too.


## Block Diagram:
<img width="938" height="769" alt="Screenshot 2026-11-02 at 8 35 20 am" src="https://github.com/user-attachments/assets/e6e80692-d0e1-4b9d-8aa8-8bbab5e83df1" />
