# NumWorks N0100 Power Module — Design Spec

## Purpose
Internal daughter board replacing the broken RT9526A charger on a NumWorks N0100 calculator.
Also adds 5V regulated output for a Raspberry Pi Zero 2W mounted inside the calculator.

## Target Hardware
- **Calculator:** NumWorks N0100 (STM32F412, micro-USB, 1820mAh Li-Ion battery, 2.8V logic rail)
- **Schematics:** https://tiplanet.org/forum/archives_voir.php?id=2637409

## What This Board Does
1. **Li-Ion charging** — TP4056 linear charger, 500mA from USB
2. **Battery protection** — DW01A + FS8205A (over-charge, over-discharge, over-current, short-circuit)
3. **5V buck-boost** — TPS63020, 3.0–4.2V → 5.0V for Pi Zero 2W (up to 2A transient)
4. **Battery monitoring** — 1:1 voltage divider for STM32 ADC

## What This Board Does NOT Include
- ❌ USB connector (on mainboard)
- ❌ JST battery connector (wires/solder pads)
- ❌ ESD protection (USBLC6-2SC6 already on mainboard)
- ❌ 2.8V LDO (RT9078 stays on mainboard)
- ❌ Backlight driver (RT9365 stays on mainboard)

## Physical Constraints
- Board sits inside the calculator — must be small and flat
- No tall components, no through-hole connectors
- All connections via solder pads + wires to mainboard
- Passives: 0402/0603 preferred

## Wire Signals to Mainboard
| Signal    | Direction      | Connects To        | Notes                              |
|-----------|---------------|--------------------|------------------------------------|
| VUSB      | In from MB    | Mainboard USB 5V   | Power source for charger           |
| GND       | Common        | System ground      |                                    |
| VBAT_RAW  | Bidirectional | Battery +          | Charger output / battery input     |
| BAT_NEG   | To battery    | Battery −          | Through protection MOSFETs         |
| V5_PI     | Out to Pi     | Pi Zero 5V rail    | TPS63020 output                    |
| PI_EN     | In from STM32 | STM32 PB9          | High = enable Pi power             |
| CHG_STAT  | Out to STM32  | STM32 PA0          | Active-low charging indicator      |
| VBAT_SNS  | Out to STM32  | STM32 PA1          | Battery voltage / 2 (ADC input)    |

## ICs
| IC          | Function              | Package   | LCSC     |
|-------------|----------------------|-----------|----------|
| TP4056      | Li-Ion charger       | ESOP-8    | C16581   |
| DW01A       | Battery protection   | SOT-23-6  | C351410  |
| FS8205A     | Dual N-MOSFET        | SOT-23-6  | C32254   |
| TPS63020    | Buck-boost converter | VSON-14   | C15483   |

## Key Design Values
- **Charge current:** 500mA (R_PROG = 2kΩ)
- **Buck-boost output:** 5.045V (R_top = 1MΩ, R_bot = 110kΩ)
- **PI_EN default:** OFF (100kΩ pull-down, STM32 drives high)
- **PS/SYNC:** Forced PWM mode (100kΩ pull-down)
- **Battery monitor:** 1:1 divider (2× 1MΩ) + 100nF filter → VBAT/2 at ADC
- **Inductor:** 2.2µH, 3A rated
- **Current sense:** 100Ω between battery − and DW01A VM pin

## Power Budget (1820mAh battery)
- Calculator only: ~90mA → ~20h runtime
- Pi idle: ~250mA → ~5h runtime (from ~1450mAh usable)
- Pi + calc active: ~350mA → ~4h runtime

## Existing Mainboard Components (kept)
- **RT9078:** 2.8V LDO for STM32 logic
- **RT9365:** Backlight LED driver
- **USBLC6-2SC6:** USB ESD protection
