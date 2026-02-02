#!/usr/bin/env python3
"""Fix PCB layout: proper pad spacing, clean component placement, remove bad routing."""
import re

PCB_PATH = "layouts/default/default.kicad_pcb"

with open(PCB_PATH) as f:
    content = f.read()

# ============================================================
# 1. Remove ALL traces, vias, and zones (bad programmatic routing)
# ============================================================
# Remove segments (traces)
content = re.sub(r'\t\(segment\s.*?\)\n', '', content)
# Remove vias
content = re.sub(r'\t\(via\s.*?\)\n', '', content)
# Remove zones (ground pour) - multiline
content = re.sub(r'\t\(zone\s.*?\n(?:\t\t.*\n)*?\t\)\n', '', content)

# ============================================================
# 2. Fix solder pad positions - evenly spaced along bottom edge
# ============================================================
# Board is 30x18mm, origin at (100, 80), so bottom edge is y=98
# Pads along bottom, from left to right, 2.5mm from edge (y=95.5)
# Spread across the board width: x from 103 to 127, 6 pads = 4.8mm spacing

pad_positions = {
    "pad_vusb":     (103.0, 95.5),
    "pad_gnd":      (107.8, 95.5),
    "pad_vbat":     (112.6, 95.5),
    "pad_pi_en":    (117.4, 95.5),
    "pad_v5_pi":    (122.2, 95.5),
    "pad_chg_stat": (127.0, 95.5),
}

for pad_name, (x, y) in pad_positions.items():
    # Find the footprint block for this pad by atopile_address
    pattern = rf'(\(footprint "SolderPad:SolderPad".*?atopile_address" "{pad_name}".*?)\(at [\d\.]+ [\d\.]+\)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        old = match.group(0)
        new = match.group(1) + f'(at {x} {y})'
        content = content.replace(old, new, 1)
        print(f"  Moved {pad_name} -> ({x}, {y})")
    else:
        print(f"  WARNING: Could not find {pad_name}")

# ============================================================
# 3. Fix component positions for better layout
# ============================================================
# Board: 30x18mm, origin (100, 80)
# Left zone (charger): x=100-110
# Center zone (MOSFET): x=110-115  
# Right zone (boost): x=115-130

component_positions = {
    # Charger zone - TP4056 centered
    "charger.ic":      (105.0, 86.5, 0),     # U2 - TP4056
    "charger.r_prog":  (101.5, 89.5, 0),     # R5 - 2k PROG resistor, near PROG pin
    "charger.c_in":    (109.0, 84.0, 90),    # C6 - input cap near VCC
    "charger.c_bat":   (109.0, 89.5, 90),    # C5 - battery cap near BAT

    # MOSFET zone
    "power_sw.mosfet": (113.0, 86.5, 0),     # Q1 - AO3401A
    "power_sw.r_pu":   (113.0, 83.5, 0),     # R8 - 100k pull-up

    # Boost zone - SX1308 + inductor + diode
    "boost.l1":        (117.5, 86.5, 0),     # L1 - inductor, close to SX1308 VIN/SW
    "boost.ic":        (121.5, 86.5, 0),     # U1 - SX1308
    "boost.d1":        (125.0, 84.0, 0),     # D1 - SS34 diode, SW to VOUT
    "boost.c_in":      (117.5, 83.0, 90),    # C1 - 10uF input cap
    "boost.c_out":     (128.0, 86.5, 90),    # C2 - 22uF output cap
    "boost.r_fb_top":  (124.5, 89.5, 90),    # R3 - 220k feedback top
    "boost.r_fb_bot":  (126.5, 89.5, 90),    # R2 - 30k feedback bottom
}

for ato_addr, pos in component_positions.items():
    x, y = pos[0], pos[1]
    rot = pos[2] if len(pos) > 2 else 0
    
    pattern = rf'(\(footprint "[^"]*".*?atopile_address" "{ato_addr}".*?)\(at [\d\.]+ [\d\.]+(?: [\d]+)?\)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        old = match.group(0)
        rot_str = f' {rot}' if rot else ''
        new = match.group(1) + f'(at {x} {y}{rot_str})'
        content = content.replace(old, new, 1)
        print(f"  Placed {ato_addr} -> ({x}, {y}, rot={rot})")
    else:
        print(f"  WARNING: Could not find {ato_addr}")

# ============================================================
# 4. Remove old board outline and add new one
# ============================================================
# Remove existing Edge.Cuts lines
content = re.sub(r'\t\(gr_line\s*\(start[^)]*\)\s*\(end[^)]*\)\s*\(stroke[^)]*\(type[^)]*\)\)\s*\(layer "Edge\.Cuts"\).*?\)\n', '', content)
content = re.sub(r'\t\(gr_arc\s*\(start[^)]*\)\s*\(mid[^)]*\)\s*\(end[^)]*\)\s*\(stroke[^)]*\(type[^)]*\)\)\s*\(layer "Edge\.Cuts"\).*?\)\n', '', content)
content = re.sub(r'\t\(gr_rect\s*\(start[^)]*\)\s*\(end[^)]*\)\s*\(stroke[^)]*\(type[^)]*\)\)\s*\(fill[^)]*\)\s*\(layer "Edge\.Cuts"\).*?\)\n', '', content)

# Board outline: 30x18mm at (100, 80)
board_outline = """
	(gr_line (start 100 80) (end 130 80) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "b0010001-0000-0000-0000-000000000001"))
	(gr_line (start 130 80) (end 130 98) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "b0010002-0000-0000-0000-000000000002"))
	(gr_line (start 130 98) (end 100 98) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "b0010003-0000-0000-0000-000000000003"))
	(gr_line (start 100 98) (end 100 80) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "b0010004-0000-0000-0000-000000000004"))
"""

# ============================================================
# 5. Remove old silkscreen text and add clean labels
# ============================================================
content = re.sub(r'\t\(gr_text\s"[^"]*".*?\)\)\n', '', content, flags=re.DOTALL)

# Pad labels - positioned above each pad (y = 93.5, pads at 95.5)
labels = [
    ("VUSB", 103.0, 93.8),
    ("GND",  107.8, 93.8),
    ("VBAT", 112.6, 93.8),
    ("EN",   117.4, 93.8),
    ("5V",   122.2, 93.8),
    ("CHG",  127.0, 93.8),
]

silkscreen = ""
uid_counter = 0xa001

for text, x, y in labels:
    silkscreen += f'\t(gr_text "{text}" (at {x} {y}) (layer "F.SilkS") (uuid "{uid_counter:08x}-0000-0000-0000-000000000001")\n'
    silkscreen += f'\t\t(effects (font (size 0.8 0.8) (thickness 0.15)) (justify bottom))\n\t)\n'
    uid_counter += 1

# Board title
silkscreen += f'\t(gr_text "NW-PWR" (at 103 81.2) (layer "F.SilkS") (uuid "a0010010-0000-0000-0000-000000000001")\n'
silkscreen += f'\t\t(effects (font (size 1 1) (thickness 0.15)))\n\t)\n'

# Insert before the closing parenthesis
content = content.rstrip()
if content.endswith(')'):
    content = content[:-1] + board_outline + silkscreen + ')\n'

with open(PCB_PATH, 'w') as f:
    f.write(content)

print("\nDone! Layout fixed:")
print("  - Removed all traces/vias/zones (route manually in KiCad)")
print("  - 6 solder pads evenly spaced along bottom edge")
print("  - Components grouped by function")
print("  - Clean silkscreen labels")
print("  - 30x18mm board outline")
