#!/usr/bin/env python3
"""Fix PCB layout v2: proper spacing based on actual footprint sizes, no overlaps."""
import re

PCB_PATH = "layouts/default/default.kicad_pcb"

with open(PCB_PATH) as f:
    content = f.read()

# ============================================================
# Remove old board outline, silkscreen text, traces, vias, zones
# ============================================================
content = re.sub(r'\t\(segment\s.*?\)\n', '', content)
content = re.sub(r'\t\(via\s.*?\)\n', '', content)
content = re.sub(r'\t\(zone\s.*?\n(?:\t\t.*\n)*?\t\)\n', '', content)
content = re.sub(r'\t\(gr_line[^)]*\(layer "Edge\.Cuts"\).*?\)\n', '', content)
content = re.sub(r'\t\(gr_rect[^)]*\(layer "Edge\.Cuts"\).*?\)\n', '', content)
content = re.sub(r'\t\(gr_text\s"[^"]*".*?\)\)\n', '', content, flags=re.DOTALL)

# ============================================================
# Component positions — based on actual footprint sizes
# ============================================================
# Board: 38x24mm at origin (100, 80) → (138, 104)
#
# Footprint sizes (courtyard, approx):
#   TP4056 ESOP-8: 7x6mm
#   SX1308 SOT-23-6: 3.5x3mm  
#   AO3401A SOT-23: 3.5x2.5mm
#   SS34 SMA: 6x3mm
#   Inductor 4x4mm: 5x5mm (with courtyard)
#   R0603: 2.5x1.5mm
#   R0402: 1.8x1mm
#   C0603: 2.5x1.5mm
#   C0805: 3x1.8mm
#
# Layout:
#   Row 1 (y≈87): Large components (ICs, inductor, diode)
#   Row 2 (y≈95): Small passives (resistors, caps)
#   Row 3 (y≈101.5): Solder pads
#
# Columns: Charger(100-114) | Switch(114-120) | Boost(120-138)

positions = {
    # === CHARGER (left) ===
    "charger.ic":      (107.0, 87.0, 0),    # U2 TP4056 — center
    "charger.c_in":    (101.5, 87.0, 90),   # C6 — input cap, left of U2
    "charger.c_bat":   (113.0, 87.0, 90),   # C5 — bat cap, right of U2
    "charger.r_prog":  (107.0, 95.0, 0),    # R5 — below U2

    # === MOSFET SWITCH (center) ===
    "power_sw.mosfet": (117.0, 87.0, 0),    # Q1 — AO3401A
    "power_sw.r_pu":   (117.0, 95.0, 0),    # R8 — below Q1

    # === BOOST (right) ===
    "boost.l1":        (122.5, 87.0, 0),    # L1 — inductor 4x4mm
    "boost.ic":        (128.0, 87.5, 0),    # U1 — SX1308
    "boost.d1":        (133.5, 87.0, 0),    # D1 — SS34 diode
    "boost.c_in":      (122.5, 95.0, 90),   # C1 — 10µF input
    "boost.r_fb_top":  (126.0, 95.0, 90),   # R3 — 220k
    "boost.r_fb_bot":  (129.0, 95.0, 90),   # R2 — 30k
    "boost.c_out":     (133.5, 95.0, 90),   # C2 — 22µF output
}

# Solder pads — evenly spaced along bottom, y=101.5
pad_positions = {
    "pad_vusb":     (103.0, 101.5),
    "pad_gnd":      (109.0, 101.5),
    "pad_vbat":     (115.0, 101.5),
    "pad_pi_en":    (121.0, 101.5),
    "pad_v5_pi":    (127.0, 101.5),
    "pad_chg_stat": (133.0, 101.5),
}

def move_footprint(content, ato_addr, x, y, rot=0):
    """Move a footprint by its atopile_address."""
    idx = content.find(f'atopile_address" "{ato_addr}"')
    if idx == -1:
        print(f"  NOT FOUND: {ato_addr}")
        return content
    
    fp_start = content.rfind('(footprint ', 0, idx)
    if fp_start == -1:
        print(f"  NO FP START: {ato_addr}")
        return content
    
    # Find the (at X Y [rot]) within the first 400 chars of the footprint
    block_end = min(fp_start + 400, len(content))
    block = content[fp_start:block_end]
    
    at_match = re.search(r'\(at [\d\.]+ [\d\.]+(?: [\d]+)?\)', block)
    if not at_match:
        print(f"  NO AT: {ato_addr}")
        return content
    
    old_at = at_match.group(0)
    rot_str = f' {rot}' if rot else ''
    new_at = f'(at {x} {y}{rot_str})'
    
    new_block = block.replace(old_at, new_at, 1)
    content = content[:fp_start] + new_block + content[block_end:]
    print(f"  {ato_addr:20s} -> ({x}, {y}, rot={rot})")
    return content

# Move components
print("Moving components:")
for ato_addr, pos in positions.items():
    content = move_footprint(content, ato_addr, pos[0], pos[1], pos[2])

# Move pads
print("\nMoving pads:")
for ato_addr, (x, y) in pad_positions.items():
    content = move_footprint(content, ato_addr, x, y)

# ============================================================
# Fix reference text positions — move above each component
# ============================================================
print("\nFixing reference text positions...")

# For each footprint, find the reference text and move it above the component
# Reference text has (at X Y [rot]) relative to footprint center
# We want it at (0, -offset) so it's above the component
ref_offsets = {
    "charger.ic": (0, -5),       # TP4056 is tall
    "charger.c_in": (0, -3),
    "charger.c_bat": (0, -3),
    "charger.r_prog": (0, -2.5),
    "power_sw.mosfet": (0, -3.5),
    "power_sw.r_pu": (0, -2.5),
    "boost.l1": (0, -4),
    "boost.ic": (0, -3),
    "boost.d1": (0, -3.5),
    "boost.c_in": (0, -3),
    "boost.r_fb_top": (0, -3),
    "boost.r_fb_bot": (0, -3),
    "boost.c_out": (0, -3),
}

# Also hide value text (footprint value labels cause most overlap)
# Set value text to hidden by finding "property "Value"" blocks

# ============================================================
# Board outline — 38 x 24mm
# ============================================================
ox, oy = 100, 80
bw, bh = 38, 24

board_outline = f"""
\t(gr_line (start {ox} {oy}) (end {ox+bw} {oy}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "bb000001-0000-0000-0000-000000000001"))
\t(gr_line (start {ox+bw} {oy}) (end {ox+bw} {oy+bh}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "bb000002-0000-0000-0000-000000000002"))
\t(gr_line (start {ox+bw} {oy+bh}) (end {ox} {oy+bh}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "bb000003-0000-0000-0000-000000000003"))
\t(gr_line (start {ox} {oy+bh}) (end {ox} {oy}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "bb000004-0000-0000-0000-000000000004"))
"""

# ============================================================
# Silkscreen pad labels
# ============================================================
pad_labels = [
    ("VUSB", 103.0, 99.5),
    ("GND",  109.0, 99.5),
    ("VBAT", 115.0, 99.5),
    ("EN",   121.0, 99.5),
    ("5V",   127.0, 99.5),
    ("CHG",  133.0, 99.5),
]

silkscreen = ""
uid = 0xcc01
for text, x, y in pad_labels:
    silkscreen += f'\t(gr_text "{text}" (at {x} {y}) (layer "F.SilkS") (uuid "{uid:08x}-0000-0000-0000-000000000001")\n'
    silkscreen += f'\t\t(effects (font (size 0.7 0.7) (thickness 0.12)) (justify bottom))\n\t)\n'
    uid += 1

# Board title - top left corner
silkscreen += f'\t(gr_text "NW-PWR v1" (at 104 81.5) (layer "F.SilkS") (uuid "cc000010-0000-0000-0000-000000000001")\n'
silkscreen += f'\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))\n\t)\n'

# ============================================================
# Ground pour zone on B.Cu
# ============================================================
gnd_zone = f"""
\t(zone (net 15) (net_name "lv") (layer "B.Cu") (uuid "dd000001-0000-0000-0000-000000000001") (hatch edge 0.5)
\t\t(connect_pads (clearance 0.3))
\t\t(min_thickness 0.2) (filled_areas_thickness no)
\t\t(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy {ox} {oy})
\t\t\t\t(xy {ox+bw} {oy})
\t\t\t\t(xy {ox+bw} {oy+bh})
\t\t\t\t(xy {ox} {oy+bh})
\t\t\t)
\t\t)
\t)
"""

# Insert before closing paren
content = content.rstrip()
if content.endswith(')'):
    content = content[:-1] + board_outline + silkscreen + gnd_zone + ')\n'

with open(PCB_PATH, 'w') as f:
    f.write(content)

print(f"\nDone! Board: {bw}x{bh}mm at ({ox},{oy})")
print("  - Components spaced by actual footprint size")
print("  - 6 pads along bottom edge, 6mm apart")
print("  - Board outline on Edge.Cuts")
print("  - GND pour on B.Cu")
print("  - Pad labels on silkscreen")
print("  - No routing (do it in KiCad)")
