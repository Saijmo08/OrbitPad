# OrbitPad

OrbitPad is a 12-key (4 × 3) USB macropad based on a Raspberry Pi Pico. Its design includes two rotary-encoder connections, a separate layer button, an RGB LED connection, a seven-pin OLED connection, a printed enclosure, and a Windows configuration app. Key actions, profiles, and layers are stored in a CSV file on the board; the desktop app transfers changes over the Pico's **USB CDC data port**.

> **Project status — read before manufacturing or submitting:** The CAD, KiCad source files, Gerbers, case-part STEP exports, and CircuitPython/KMK sources are in this project. This is **not yet a verified production release**. The current firmware deliberately disables OLED output (`OLED_ENABLED = False`), the Ctrl+Z/Y behaviour on German keyboard layouts has not been confirmed/fixed, and the PCB schematic and layout have different switch/diode reference numbering. Run a fresh schematic/PCB synchronization, KiCad DRC and physical-fit check before using the Gerbers. The four submission screenshots listed below are not in the provided repository archive.

## At a glance

- **12 configurable matrix keys.** The app numbers the physical positions down each column:

  ```text
    1   5   9
    2   6  10
    3   7  11
    4   8  12
  ```

- **Profiles and layers:** each profile contains one or more layers of 12 assignments. The *separate* GP9 button advances through that profile's layers; key 12 is an ordinary assignable key. GP15 selects maintenance mode when USB is plugged in, and the Pico's BOOTSEL button is for firmware recovery/flashing. These are three distinct controls.
- **Two external encoder connections:** the firmware maps encoder 1 to volume down/up/mute and encoder 2 to previous/next/play-pause. The schematic and PCB expose the encoder pins on J2 and J3; the encoder bodies are not PCB-mounted footprints.
- **Addressable RGB output:** GP19 feeds an external 12-pixel chain via J4. The firmware limits LED brightness; check LED supply, data-high compatibility and USB current before assembly.
- **OLED interface:** J1 routes the 128 × 128 SSD1351 module's seven signals. Screen-layout previews are present, but the physical panel has not displayed framebuffer images reliably. The current firmware does **not** drive it, and the app does **not** upload screen assets during Save on Pad. Do not use a preview image as evidence of a working OLED.

### Software-rendered screen previews

These images are configurator mock-ups, **not photographs of the assembled hardware**:

| Default | KiCad | Test |
|:--:|:--:|:--:|
| ![Default-layer software preview](firmware/Configuration%20App/previews/screen_0_0.png) | ![KiCad-layer software preview](firmware/Configuration%20App/previews/screen_1_0.png) | ![Test-layer software preview](firmware/Configuration%20App/previews/screen_2_0.png) |

### Required submission images — still to add

Before submitting, take or export **actual** images and add them to `assets/submission/`, then embed them here. The provided archive's `assets/` directory is empty.

| Required view | Suggested file | How to create it |
|---|---|---|
| Complete assembled hackpad | `assets/submission/assembled-pad.jpg` | Photo or an accurately labelled full-assembly CAD render. |
| Schematic | `assets/submission/schematic.png` | Screenshot/export from `pcb/Macro Pad.kicad_sch`. |
| PCB layout | `assets/submission/pcb.png` | Screenshot/export from `pcb/Macro Pad.kicad_pcb` with board outline and copper visible. |
| Case with PCB fit | `assets/submission/case-fit.png` | Screenshot/render of `cad/Macro Pad Case.step` showing the PCB inside the enclosure. |

**Do not submit the OLED previews above in place of those four views.** Once the real files exist, add Markdown image links for all four here and verify that they render on GitHub.

## Repository map

```text
cad/
  Macro Pad Case.step                   assembled enclosure CAD, includes PCB/Pico models
pcb/
  Macro Pad.kicad_pro                   KiCad 9 project
  Macro Pad.kicad_sch                   schematic source
  Macro Pad.kicad_pcb                   PCB layout source
  Macro Pad.step                        exported PCB assembly
  libraries/custom/scot/               included third-party KiCad assets
firmware/
  Configuration App/                   Windows Python app sources and local CSV
  kmk/                                 KMK keyboard framework source
production/
  board/hardware/                      Gerber ZIP + individual printable STEP parts
  board/software/                      Pico UF2, boot.py, code.py, lib/, screens/
  Configuration App/                   Windows executable and a copy of app sources
  README.md                            fabrication and installation instructions
assets/                                 add real submission images here
```

Use the **source files** in `pcb/`, `cad/`, and `firmware/` for editing. See [production/README.md](production/README.md) for what to manufacture, what to copy onto the Pico, and how to launch the app. `production/board/software/` does **not** contain the KMK package; a fresh Pico installation must also copy `firmware/kmk/` to `CIRCUITPY/kmk/`.

## Preliminary bill of materials

Quantities below are derived from the KiCad schematic/PCB **or** the intended external connections. They are **not** a purchasable, approved-parts-list BOM: actual manufacturer part numbers, supply choices, mounting hardware, and switch hot-swap method still need to be specified. The schematic and PCB references for the 12 switches/diodes currently disagree; the quantities match, but references must be reconciled.

| Qty | Part / function | Design references / notes |
|---:|---|---|
| 1 | Raspberry Pi Pico | A1; the standard Pico has **micro-USB**, and the PCB has no separate USB-C connector. If a USB-C Pico-compatible variant is intended, specify it and verify the footprint/case fit. |
| 12 | MX-compatible mechanical switches and suitable keycaps | PCB S2–S13; schematic S13–S24. The placed switch footprint has through-hole electrical pads, **not a dedicated hot-swap-socket footprint**; decide and verify the socket method before claiming hot-swap support. |
| 12 | Through-hole diodes compatible with the DO-35 footprint | PCB D1–D12; schematic D13 and D15–D25. Check orientation and choose an exact diode part. |
| 2 | 6 mm through-hole pushbuttons | SW13 (GP9 layer) and SW16 (GP15 maintenance). The Pico's own BOOTSEL button is separate. |
| 1 | 100 µF radial capacitor | C1, between VBUS and GND; verify voltage rating and polarity. |
| 1 | Seven-pin 1.00 mm OLED header and compatible SSD1351 module | J1; the OLED is off-board and currently disabled in firmware. |
| 2 | Six-pin 2 × 3, 1.00 mm headers and compatible rotary encoders | J2/J3; encoders are wired externally. Verify physical connector orientation. |
| 1 | Three-pin 1.00 mm RGB header and external 12-pixel addressable LED chain | J4; powered from Pico VBUS. Verify logic levels/current. |
| 1 set | Case parts, mounting hardware and USB data cable | `Top.step`, `Bottom.step`, `Button.step`, `Button Stick.step`; check required quantities, print tolerances and assembly fit. |

## Firmware and configurator

The production software is **CircuitPython + KMK**, not a compiled OrbitPad UF2. The supplied `.uf2` is the CircuitPython interpreter for a Raspberry Pi Pico. `production/board/software/code.py` is the OrbitPad application. Install it with `boot.py`, the bundled `.mpy` libraries and **`firmware/kmk/`** as described in [production/README.md](production/README.md).

On Windows, use the Python source app at `firmware/Configuration App/main.py` with `requirements.txt`, or treat the included `production/Configuration App/Configuration App.exe` as **unverified** until its data-file location and persistence have been tested. The app's `Apply` button saves the **local** CSV. `Save on Pad` transfers that CSV over a verified **USB CDC DATA** COM port, activates the selected profile and stores that profile as the next boot selection. A profile opens on its first layer after reboot. Only the text in **Shortcut** generates a HID action; icons/titles are labels.

> On a German QWERTZ host, `Ctrl+Z`/`Ctrl+Y` may be interpreted differently because USB keyboard usages describe physical key positions. A reported symptom is that the supposed Undo macro may act like Redo after a manual Undo. Verify the active Windows layout and test in an editor before declaring the shortcuts correct. The repository snapshot does not include a confirmed layout fix.

## Design validation / release checklist

- [ ] Compare the schematic against the PCB in KiCad 9. The schematic uses `S13–S24` and `D13, D15–D25`, while the PCB uses `S2–S13` and `D1–D12`; update/link footprints deliberately and check nets before exporting fresh Gerbers.
- [ ] Run schematic ERC and **PCB DRC with zero errors**; save the resulting reports/evidence. No DRC result was supplied in the reviewed archive.
- [ ] Check the assembled case/PCB clearance (about 0.2 mm or the printer-appropriate value), mounting points, switch retention, button travel, encoder position and accessible Pico BOOTSEL/GP15. A STEP file alone does not prove fit.
- [ ] Identify the exact controller board: a standard Raspberry Pi Pico has **micro-USB**, although USB-C was requested. No standalone USB-C connector footprint is present; confirm any USB-C Pico variant fits the footprint and case.
- [ ] Decide whether/how the MX switches are hot-swappable and document the exact sockets/footprint compatibility.
- [ ] Verify LED power and GP19 3.3 V data-high compatibility with the chosen VBUS-powered RGB pixels.
- [ ] Select exact manufacturer parts and check them against the **current** approved parts list; this cannot be inferred from generic footprint names.
- [ ] After PCB fixes, regenerate `production/board/hardware/gerbers.zip` from the **final** board and verify the drill, outline, mask, copper and silkscreen files. The archive currently has an older `Macro_Pad.zip`, not the checklist's requested filename.
- [ ] Add the four required real submission images above; verify the physical key, encoder, layer and app behaviour; document the OLED limitation honestly.
- [ ] Commit and push **all necessary** CAD, KiCad, firmware, production files, images and these READMEs. In the supplied ZIP's Git snapshot, `HEAD` contains only six tracked paths, not the design/manufacturing tree; check the actual remote after pushing.

Third-party KMK and KiCad libraries are included. Review their upstream licenses/attribution and add a license for your own project before publishing. No project-level license was present in the provided archive.
