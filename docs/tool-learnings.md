# PCB Design Tools — Learnings & Comparison

## Project Context
- **Goal:** Internal daughter board for NumWorks N0100 calculator
- **Function:** TP4056 charger + DW01A/FS8205A protection + TPS63020 5V boost for Raspberry Pi Zero 2W
- **Key constraint:** This is an INTERNAL board — no USB connector, no battery connector (JST), no ESD. VUSB comes via wire from mainboard. Battery connects directly via solder pads/wires. Minimal connectors.
- **Board sits inside the calculator** — space is extremely limited

## What NOT to Include
- ❌ USB connector (already on mainboard)
- ❌ JST battery connector (battery soldered/wired directly)
- ❌ ESD protection (already on mainboard)
- ❌ Excessive through-hole pin headers — use solder pads or minimal flat connectors
- The board should be as small and flat as possible

## Tool 1: Zener (Diode `pcb` CLI)

### What It Is
- Rust CLI tool from [Diode Inc](https://github.com/diodeinc/pcb)
- HDL language (`.zen` files) based on Starlark (Python-like)
- Version: 0.3.31
- ~Newer, smaller community

### What Works
- `pcb build` — compiles .zen to netlist, validates, generates BOM
- `pcb layout` — places all footprints with net assignments into a `.kicad_pcb`
- `pcb bom` — auto-matches generic passives to real MPNs (Murata caps, Panasonic resistors)
- `pcb search` — component search
- References KiCad symbol/footprint libraries directly (`@kicad-symbols/`, `@kicad-footprints/`)
- **VSCode extension** (`diode-inc.zener`) renders .zen as interactive schematics — **this is the visualization solution**

### What Doesn't Work Well
- Layout is grid-placed only (no intelligent grouping or autorouting)
- No CLI schematic export (must use VSCode extension for visual schematics)
- Custom components with `Symbol(definition=...)` work for build but don't get real KiCad symbols in schematic view
- Auth required for some features — login via `pcb auth login` (browser OAuth flow)

### Auth Status
- Martin has an account on the Mac (email: dolezelektricm@gmail.com)
- Token refreshes with `pcb auth refresh`
- **Server needs its own login** — can be done via browser, needs email OTP

### Key Syntax
```python
# Generics (auto-matched to real parts)
Resistor = Module("@stdlib/generics/Resistor.zen")
Capacitor = Module("@stdlib/generics/Capacitor.zen")

# KiCad library components
Component(
    name = "U1",
    symbol = Symbol(library = "@kicad-symbols/Battery_Management.kicad_sym", name = "DW01A"),
    footprint = File("@kicad-footprints/Package_TO_SOT_SMD.pretty/SOT-23-6.kicad_mod"),
    mpn = "DW01A",
    pins = { "VCC": vcc_net, "GND": gnd_net, ... },
)

# Nets
gnd = Ground("GND")
vcc = Power("VCC", voltage = VoltageRange("3.0V to 4.2V"))
my_net = Net("MY_NET")
```

### Project Location
- Workspace: `~/clawd/numworks-power-pcb/`
- GitHub: `elektricM/numworks-power-pcb`
- Entry: `boards/PowerModule/PowerModule.zen`

---

## Tool 2: atopile

### What It Is
- Python-based PCB design language (`.ato` files)
- From [atopile](https://github.com/atopile/atopile) — ~3k GitHub stars
- Version: 0.12.5 (latest: 0.14.0)
- More active community, Discord, package registry

### What Works
- `ato create part` — fetches component from JLCPCB/LCSC by part number, auto-generates footprint + symbol + 3D model
- `ato build` — compiles, picks passive components automatically from JLCPCB library
- `ato view` — schematic/block diagram visualization
- **VSCode/Cursor extension** available
- Package registry at packages.atopile.io
- Has MCP server for AI coding assistance

### What Doesn't Work Well (v0.12.5)
- `Resistor`, `Capacitor`, `Inductor` are NOT importable from `"generics/*.ato"` — the import path is wrong or they're Python-native classes in faebryk
- The `#pragma experiment("TRAITS")` flag is needed for component traits
- Interactive CLI (`ato create part`) doesn't work well in non-interactive/piped mode
- KiCad plugin installation fails on headless server (needs KiCad config path)

### Auth
- No auth needed for basic usage
- JLCPCB component fetch works without login

### Key Syntax
```
#pragma experiment("TRAITS")

module MyCircuit:
    signal vcc
    signal gnd

    r1 = new Resistor
    r1.resistance = 10kohm +/- 5%
    r1.package = "0603"
    r1.p1 ~ vcc
    r1.p2 ~ gnd

    ic = new MyCustomComponent
    ic.VIN ~ vcc
    ic.GND ~ gnd
```

### Component Creation
```bash
# Search by LCSC part number
ato create part  # then enter C16581 for TP4056

# Successfully fetched:
# - C16581 → TP4056 (TOPPOWER)
# - C351410 → DW01A (PUOLOP)
# - C32254 → FS8205A (Fortune Semicon)
# - C15483 → TPS63020DSJR (Texas Instruments)
```

### Project Location
- Workspace: `~/clawd/numworks-power-ato/`
- Not yet on GitHub

---

## Comparison

| Feature | Zener | atopile |
|---------|-------|---------|
| Language | Starlark (.zen) | Custom (.ato) |
| Community | Smaller | ~3k stars, active |
| Passive auto-pick | ✅ Via stdlib generics | ✅ Via JLCPCB database |
| Component fetch | Manual symbol/footprint | `ato create part` (auto) |
| Schematic view | VSCode extension | `ato view` + VSCode |
| KiCad output | ✅ .kicad_pcb | ✅ .kicad_pcb |
| BOM | ✅ Great | ✅ Auto from JLCPCB |
| Layout | Grid placement | Grid placement |
| Maturity | Newer | More mature |
| Docs | Embedded (`pcb doc`) | docs.atopile.io |

## Recommendation
Both tools produce KiCad PCB output with grid-placed footprints. Manual routing in KiCad is needed either way.

**atopile** has the edge for:
- Larger community, more examples
- Better component fetching (LCSC/JLCPCB integrated)
- `ato view` for visualization without needing VSCode
- Auto parametric picking of discretes

**Zener** has the edge for:
- Direct KiCad library integration
- BOM with real MPN matching
- Slightly cleaner syntax
- Built-in simulation (`pcb sim`)

## Next Steps
1. Pick one tool (recommend trying atopile v0.14.0 for better stability)
2. Design the circuit with MINIMAL connectors — just solder pads for wires
3. Get schematic visualization working first
4. Then proceed to layout
