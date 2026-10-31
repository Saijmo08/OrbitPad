# OrbitPad

OrbitPad is a 12-key macropad built around a Raspberry Pi Pico. It combines two rotary encoders, a separate layer button, an external RGB LED chain, and an OLED connector with a Windows app for editing shortcuts and profiles.

> **Current status:** The keyboard and configurator code is included, but the OLED is disabled in this firmware because its physical framebuffer output has not been verified. This is a project in progress, **not** a tested manufacturing release.

<!-- Add an actual photo here before submitting:
![Assembled OrbitPad](assets/submission/assembled-pad.jpg)
-->
**TODO:** photograph the assembled pad and show it here.

## Features

- **12 configurable keys** arranged as four rows and three columns. The app numbers them **down** each column:

  ```text
   1   5   9
   2   6  10
   3   7  11
   4   8  12
  ```

- **Profiles and layers:** each profile can contain different 12-key layouts. The separate button on GP9 cycles layers; key 12 is an ordinary assignable key.
- **Two external rotary encoders:** currently mapped to volume/mute and media playback controls.
- **12 external addressable RGB LEDs:** connected through the PCB's J4 header and driven from GP19.
- **128 × 128 OLED connection:** a seven-pin J1 header and screen-layout previews exist, but the actual display output is **not working in the current release**.
- **Windows configurator:** set a shortcut per key, then send the CSV to the pad over its USB CDC **data** port. Saving also remembers the selected profile for the next boot.

## CAD Model

The complete assembly is [`cad/Macro Pad Case.step`](cad/Macro%20Pad%20Case.step); its STEP model contains the enclosure, PCB and Pico models. The printable parts are [`Top.step`, `Bottom.step`, `Button.step`, and `Button Stick.step`](production/board/hardware/).

Before printing a full set, check clearances and mounting on a test print—especially PCB fit, switch retention, button travel and access to BOOTSEL. The suggested 0.2 mm clearance has **not** been verified on this design.

<!-- Add an actual CAD screenshot here before submitting:
![Case with PCB installed](assets/submission/case-fit.png)
-->
**TODO:** add a screenshot of the case with the PCB fitted inside.

## PCB

The editable design is in [`pcb/`](pcb/): [`Macro Pad.kicad_pro`](pcb/Macro%20Pad.kicad_pro), [`Macro Pad.kicad_sch`](pcb/Macro%20Pad.kicad_sch), and [`Macro Pad.kicad_pcb`](pcb/Macro%20Pad.kicad_pcb). The current [Gerber/drill ZIP](production/board/hardware/Macro_Pad.zip) is in `production/board/hardware/`.

**Pre-flight work remains:** switch/diode reference numbers differ between the schematic and PCB. Synchronize them, run KiCad ERC and a **zero-error DRC**, then export fresh Gerbers. The switch pads are through-hole; a hot-swap socket method still needs verification. The PCB uses a standard Pico footprint (standard Picos have **micro-USB**), so a requested USB-C variant would need its fit confirmed.

<!-- Add real KiCad screenshots here before submitting:
![OrbitPad schematic](assets/submission/schematic.png)
![OrbitPad PCB](assets/submission/pcb.png)
-->
**TODO:** add screenshots of the finished schematic and PCB layout.

## Firmware Overview

The Pico runs **CircuitPython + [KMK](https://github.com/KMKfw/kmk_firmware)**. Its application is `production/board/software/code.py`; `boot.py` controls the normal/maintenance USB modes. The included `.uf2` installs CircuitPython, **not** the OrbitPad app. KMK itself is in `firmware/kmk/` and must also be copied onto the Pico.

In the [Windows configurator](firmware/Configuration%20App/main.py), **Apply** saves the local CSV and **Save on Pad** uploads it. Only the **Shortcut** field sends a keystroke; icons and titles are labels. GP9 changes layers, while GP15 reveals `CIRCUITPY` when held during USB plug-in. On reboot, the last saved profile starts on its first layer.

The OLED interface remains wired but `OLED_ENABLED = False` and screen uploads are off. Also verify `Ctrl+Z`/`Ctrl+Y` under a German QWERTZ Windows layout before calling the shortcuts finished. [Installation and manufacturing details →](production/README.md)

**Software preview, not a photo of a functioning OLED:**

![OrbitPad Default profile software preview](firmware/Configuration%20App/previews/screen_0_0.png)

## BOM

A **preliminary** parts list from the KiCad design and off-board connectors; exact approved part numbers and the hot-swap method are still to be chosen:

- 1 × Raspberry Pi Pico (confirm the intended USB connector/variant)
- 12 × MX-compatible switches and 12 keycaps; hot-swap hardware **not yet specified**
- 12 × DO-35-footprint diodes
- 2 × 6 mm pushbuttons (layer and maintenance)
- 1 × 100 µF radial capacitor
- 1 × SSD1351 128 × 128 OLED module and seven-pin connector (**OLED disabled for now**)
- 2 × rotary encoders and their off-board connectors
- 12 × addressable RGB LEDs in an **external** chain and a three-pin connector
- 1 × USB data cable, case fasteners, and the printed parts listed above (verify quantities)

## Extra stuff

The [production README](production/README.md) covers board flashing, KMK installation, connector pins and the release checklist. Before submitting, add the **four real images** marked above, finish DRC and case-fit checks, and verify the BOM against the approved parts list. The three OLED images in `firmware/Configuration App/previews/` are app mock-ups, **not** hardware photographs.

Finally, commit and push the source and production folders: the Git snapshot inside the reviewed Drive ZIP tracked only six older files, not the `cad/`, `pcb/`, `firmware/` or `production/` trees. Check the live GitHub repository yourself after pushing, and add appropriate project/third-party license information.
