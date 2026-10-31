# OrbitPad production files and installation

This folder contains manufacturing exports and runnable software for OrbitPad. **Do not order the PCB from the current Gerbers yet:** the supplied schematic and PCB use different switch/diode reference ranges, and no zero-error DRC result or case-clearance verification was supplied. Follow the [project README](../README.md) and the release gates below first.

## Contents of this production folder

```text
production/
  board/
    hardware/
      Macro_Pad.zip                 current Gerber/drill archive (rename only AFTER re-export)
      Top.step
      Bottom.step
      Button.step
      Button Stick.step            separate printable case parts
    software/
      adafruit-circuitpython-raspberry_pi_pico-de_DE-10.3.1.uf2
      boot.py                      USB CDC/HID and GP15 maintenance mode
      code.py                      OrbitPad KMK firmware; OLED_ENABLED=False in this release
      orbitpad_config.csv          example assignments: copy only for a NEW install
      ssd1351_softspi.py           preserved display driver, not used while OLED off
      lib/neopixel.mpy
      lib/adafruit_pixelbuf.mpy
      screens/p0l0.bmp, p1l0.bmp, p2l0.bmp
  Configuration App/
    Configuration App.exe          Windows build; persistence NOT VERIFIED (see below)
    main.py, orbitpad_serial.py, orbitpad_screens.py, requirements.txt
    orbitpad_config.csv, icons/, fonts/, previews/
```

**Required file not copied into `production/board/software/`:** the KMK Python package is at [`../firmware/kmk/`](../firmware/kmk/). A working fresh installation must copy it as `CIRCUITPY/kmk/` as well. The `.uf2` is the **CircuitPython interpreter**, not a compiled OrbitPad application; `code.py` is the OrbitPad program.

## 1. Before ordering or printing

1. Open [`../pcb/Macro Pad.kicad_pro`](../pcb/Macro%20Pad.kicad_pro) with KiCad 9 (the design files record generator version 9.0). The PCB's 12 switches and diodes are numbered `S2–S13` / `D1–D12`; the schematic's corresponding 12 components are `S13–S24` / `D13, D15–D25`. Reconcile them with **Update PCB from Schematic**, inspecting changes rather than blindly accepting duplicate footprints. Then verify the matrix and all connector nets.
2. Run schematic **ERC** and PCB **DRC** and resolve every error; keep reports/screenshots. This archive contains no test report, and a valid Gerber ZIP is **not** evidence that DRC passes.
3. Check the full case-and-PCB assembly in [`../cad/Macro Pad Case.step`](../cad/Macro%20Pad%20Case.step). That STEP contains a PCB/Pico assembly, but clearance, hole fit, encoder height, USB connector opening, switch/socket fit and button travel have **not** been measured here. Allow an appropriate printing tolerance (the submission guidance suggests about 0.2 mm where parts meet). Verify that the Pico's BOOTSEL and GP15 service button remain usable.
4. Confirm the exact Pico variant. The standard Raspberry Pi Pico uses **micro-USB**; no separate USB-C connector is placed in the KiCad PCB. If USB-C is required, verify the actual USB-C-compatible controller's footprint and enclosure clearance before ordering.
5. The switch footprint has through-hole switch pads rather than an identified hot-swap-socket footprint. Select/verify a real hot-swap solution before advertising hot-swappable switches. Match actual diode, connector, encoder, RGB and OLED parts against your approved-parts list and the [preliminary BOM](../README.md#preliminary-bill-of-materials).
6. **Regenerate** the Gerbers and both PTH/NPTH drill files from the final DRC-clean PCB. Verify front/back copper, mask, silkscreen and `Edge.Cuts` with a Gerber viewer. Save the final archive as `production/board/hardware/gerbers.zip`. The currently supplied `Macro_Pad.zip` is a readable ZIP containing those types of layers, but is **not validated against a final, synchronized board** and is not yet named `gerbers.zip`.
7. Export the final case parts, confirm print quantities for `Button.step`/`Button Stick.step`, test the printed fit and add an assembled-pad, schematic, PCB and case-fit image to `assets/submission/` as requested in the project README.

The PCB uses third-party ScottoKeebs symbol/footprint/3D assets under `pcb/libraries/custom/scot/`. For KiCad 3D-model display, configure `SCOTTOKEEBS_KICAD` to the **absolute path** of that directory; the PCB models refer to `${SCOTTOKEEBS_KICAD}/3dmodels/...`. The files contain embedded symbols/footprints, but the repository archive does not include project-level `fp-lib-table` / `sym-lib-table`; configure the library paths if KiCad reports unresolved library items.

## 2. Fresh Raspberry Pi Pico installation

**Back up an existing Pico first.** A new UF2 flash can replace the CircuitPython filesystem and existing profiles. Do **not** overwrite a user's configured `orbitpad_config.csv`, `orbitpad_profile.json`, `orbitpad_color.json` or custom `screens/` on an already configured pad.

1. On a **standard Raspberry Pi Pico** or a confirmed pin-compatible variant, hold the Pico's **BOOTSEL** button while connecting USB. The bootloader volume (usually `RPI-RP2`) appears. Copy `board/software/adafruit-circuitpython-raspberry_pi_pico-de_DE-10.3.1.uf2` to that volume. Wait for the Pico to reboot and for `CIRCUITPY` to mount. Use an appropriate official CircuitPython build if your actual Pico variant is different; this UF2 is specifically labelled for `raspberry_pi_pico`.
2. For an **existing OrbitPad whose `CIRCUITPY` drive is hidden**, unplug USB, hold the separate **GP15** maintenance button to GND *while plugging USB back in*, then release it. `CIRCUITPY` becomes visible to Windows and host-writable. This is **not** the Pico's BOOTSEL button. Close the configurator/COM terminal before copying files.
3. From the **repository root**, copy these paths to the **root** of `CIRCUITPY` (not into a `software/` subfolder):

   ```text
   production/board/software/boot.py              -> CIRCUITPY/boot.py
   production/board/software/code.py              -> CIRCUITPY/code.py
   production/board/software/ssd1351_softspi.py   -> CIRCUITPY/ssd1351_softspi.py
   production/board/software/orbitpad_config.csv  -> CIRCUITPY/orbitpad_config.csv
   production/board/software/lib/*.mpy            -> CIRCUITPY/lib/*.mpy
   production/board/software/screens/*.bmp        -> CIRCUITPY/screens/*.bmp
   firmware/kmk/ (the WHOLE package)              -> CIRCUITPY/kmk/
   ```

   Example PowerShell commands for a **fresh/empty board** (replace `E:\` with the actual `CIRCUITPY` drive):

   ```powershell
   $drive = 'E:\'
   New-Item -ItemType Directory -Force -Path (Join-Path $drive 'lib'), (Join-Path $drive 'screens') | Out-Null
   Copy-Item -Path @('.\production\board\software\boot.py', '.\production\board\software\code.py', '.\production\board\software\ssd1351_softspi.py', '.\production\board\software\orbitpad_config.csv') -Destination $drive -Force
   Copy-Item -Force '.\production\board\software\lib\*.mpy' (Join-Path $drive 'lib')
   Copy-Item -Force '.\production\board\software\screens\*.bmp' (Join-Path $drive 'screens')
   Copy-Item -Recurse -Force '.\firmware\kmk' (Join-Path $drive 'kmk')
   ```

   If `CIRCUITPY/kmk/` already exists, **do not create `kmk/kmk/`** by copying into the old folder; compare/replace the package deliberately. On an existing pad, back up and skip the sample CSV rather than overwriting saved shortcuts.
4. Eject `CIRCUITPY` safely. **Unplug USB**, release GP15, and plug back in. A full unplug/replug is required for `boot.py` USB-device changes. In normal operation the drive is hidden; the board should expose keyboard/consumer-control HID and separate USB CDC **console** and **data** COM ports. Configuration uploads work only in normal mode, where the board can write its own filesystem. In GP15 maintenance mode the board's Python side is read-only, so **Save on Pad** is intentionally unavailable.

### Hardware connection reference (verify board orientation before plugging)

These are the PCB pad nets plus the firmware pin constants; they do not replace checking the silkscreen and the mating module's pin order.

| PCB connector | Pads and net order |
|---|---|
| J1: OLED 1×7 | 1 = Pico 3V3, 2 = GND, 3 = DIN/GP16, 4 = CLK/GP18, 5 = CS/GP17, 6 = DC/GP22, 7 = RST/GP21. Do not blindly change its 3V3 supply. |
| J2: encoder 1, 2×3 | 1 = 3V3, 2/3 = GND, 4 = button/GP20, 5 = A/GP10, 6 = B/GP11. |
| J3: encoder 2, 2×3 | 1 = 3V3, 2/3 = GND, 4 = button/GP12, 5 = A/GP13, 6 = B/GP14. |
| J4: external RGB 1×3 | 1 = VBUS (USB supply), 2 = data/GP19, 3 = GND. Confirm the chosen pixels tolerate GP19's **3.3 V** logic-high when powered from VBUS; observe USB current limits. |
| SW13 / SW16 | SW13 shorts GP9 to GND for the layer button; SW16 shorts GP15 to GND for maintenance at USB plug-in. |

Matrix rows are GP1, GP0, GP3, GP2; columns GP8, GP7, GP6 (`columns_to_anodes=True`). The app numbers keys down each column (top row 1, 5, 9). Firmware preserves OLED pin assignments, but `OLED_ENABLED = False` currently means the panel will remain blank even if J1 is wired correctly.

## 3. Windows configurator

**Recommended until the EXE is validated:** run the source app from a writable copy of the repository, not from inside the ZIP. On Windows with Python 3.10+ installed:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r '.\firmware\Configuration App\requirements.txt'
.\.venv\Scripts\python.exe '.\firmware\Configuration App\main.py'
```

Keep `main.py`, `orbitpad_serial.py`, `orbitpad_screens.py`, `orbitpad_config.csv`, `fonts/` and `icons/` together in `firmware/Configuration App/`. The requirements file currently lists `pyserial` twice with different capitalization; this should be cleaned up before a release. If automatic COM detection fails, find the Pico's **CDC DATA** (not REPL/console) port in Windows Device Manager and launch with, for example, `$env:ORBITPAD_PORT='COM4'`; the app still verifies its OrbitPad handshake.

In the app: choose a profile and layer, select a key, enter **Shortcut** (not just a title/icon), click **Apply** (saves the app's local CSV), then **Save on Pad** (uploads that CSV over CDC and persists the selected *profile* on the board). At the next restart the first layer of that profile starts. GP9 cycles layers, while key 12 remains freely assignable. Use `python '.\firmware\Configuration App\diagnose_keys.py' --port COM4` for read-only matrix/GP9 press counts; close the app first because the COM port can be opened by only one process.

**The included `Configuration App.exe` is not verified as a portable/persistent release.** Its `main.spec` is a PyInstaller one-file configuration with `datas=[]`, while app configuration is located relative to Python's `__file__`; in a one-file build that may refer to an extraction directory rather than the folder beside the EXE. Test persistence across app restarts and package/access the CSV, font and icon assets correctly before directing users to the EXE. The source-run method above has a predictable writable data directory.

**Known behaviour to test:** USB HID uses physical key positions; on a German QWERTZ Windows layout, `ctrl+z` may act as `ctrl+y` (Redo). The reported intermittent Undo behaviour after a *manual* Ctrl+Z is consistent with this, but has not been confirmed on the actual pad. Verify the active host layout and mapping before promising correct shortcuts. The current board CSV also has a copy-labelled key with `ctrl+z` instead of `ctrl+c` and a sample `strg+c` string that the firmware does not recognize as Ctrl; fix example mappings and retest before release.

## Final ship checklist

- [ ] Schematic/ERC, board synchronization and zero-error PCB DRC completed; verify final Gerbers after any edit.
- [ ] Case-assembly/PCB clearance and exact PCB thickness checked; printable STEP parts test-fitted.
- [ ] Hot-swap claim, USB connector variant, GP19 RGB logic/power and BOM part numbers resolved.
- [ ] Complete physical key/encoder/GP9, persistence and Windows layout tests performed. OLED limitation stated honestly.
- [ ] Add all four actual project screenshots and a completed approved-parts BOM to the root README.
- [ ] Make the Pico install self-contained by including/copying KMK; verify the app distribution's data persistence.
- [ ] Commit/push the design and production files; the provided ZIP's Git `HEAD` did not yet track those directories.
