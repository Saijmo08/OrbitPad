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

- **Profiles and layers:** each profile can contain different 12-key layouts. The separate button on GP9 cycles layers.
- **Two external rotary encoders:** currently mapped to volume/mute and media playback controls.
- **12 external addressable RGB LEDs:** driven from GP19.
- **128 × 128 OLED connection:** screen-layout previews exist, but the actual display output is **not working in the current release**.
- **Windows configurator:** set a shortcut per key, then send the CSV to the pad over its USB **data** port. Saving also remembers the selected profile for the next boot.

## CAD Model

The complete assembly is [`cad/Macro Pad Case.step`](cad/Macro%20Pad%20Case.step); its STEP model contains the enclosure, PCB and Pico models. The printable parts are [`Top.step`, `Bottom.step`, `Button.step`, and `Button Stick.step`](production/board/hardware/).

<img width="866" height="842" alt="Fusion360_AeaDPuZyIa" src="https://github.com/user-attachments/assets/83e3cbb1-3a5b-413f-b407-e91f67043f34" />

## PCB

The editable design is in [`pcb/`](pcb/): [`Macro Pad.kicad_pro`](pcb/Macro%20Pad.kicad_pro), [`Macro Pad.kicad_sch`](pcb/Macro%20Pad.kicad_sch), and [`Macro Pad.kicad_pcb`](pcb/Macro%20Pad.kicad_pcb). The current [Gerber/drill ZIP](production/board/hardware/Macro_Pad.zip) is in `production/board/hardware/`.

<img width="717" height="822" alt="kicad_TkNy93j8DG" src="https://github.com/user-attachments/assets/02054f75-1ab6-4698-a302-42cdd0e744f9" />

<img width="1295" height="900" alt="kicad_1az4YGjgR1" src="https://github.com/user-attachments/assets/bb4180e5-70fd-4943-942d-e75b669fd3c5" />

## Firmware Overview

The Pico runs **CircuitPython + [KMK](https://github.com/KMKfw/kmk_firmware)**. Its application is `production/board/software/code.py`; `boot.py` controls the normal USB modes. The included `.uf2` installs CircuitPython, **not** the OrbitPad app. KMK itself is in `production/board/software/kmk/` and must also be copied onto the Pico.

In the [Windows configurator](`production/Configuration App/Configuration App.exe`), **Apply** saves the local CSV and **Save on Pad** uploads it. Only the **Shortcut** field sends a keystroke, therefore icons and titles are labels. GP9 changes layers, while GP15 reveals `CIRCUITPY` when held during USB plug-in. On reboot, the last saved profile starts on its first layer.

The OLED interface remains wired but `OLED_ENABLED = False` and screen uploads are off. [Installation and manufacturing details →](production/README.md)

**Software preview:**

![OrbitPad Default profile software preview](firmware/Configuration%20App/previews/screen_0_0.png)

## BOM

A parts list from the KiCad design and off-board connectors:

- 1 × RP2040 Raspberry Pi Pico; RPI-PICO
- 12 × CHERRY MX Blue Switches; MX1A-E1NN
- 12 × Diodes, THT, 100V, 300mA, DO35; 1N4148
- 2 × 6 mm pushbuttons
- 1 × 100 µF radial capacitor
- 1 × 1.5" 128x128 OLED display module, SPI/ I2C Interface; OLED-15W-C
- 2 × rotary encoders; KY-040-2
- 1 × NeoPixel ring with 12 WS2812 5050 RGB LEDs; NEOPR12
- 1 × Adafruit MicroUSB extencion for Panel mounting; 3258

## Extra stuff

The [production README](production/README.md) covers board flashing, KMK installation and connector pins.
