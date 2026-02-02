#!/usr/bin/env python3
"""Layout v3: rounded corners, no overlaps, everything inside the board."""
import re, math

PCB_PATH = "layouts/default/default.kicad_pcb"

with open(PCB_PATH) as f:
    content = f.read()

# Clean slate: remove old outline, text, traces, vias, zones
content = re.sub(r'\t\(segment\s.*?\)\n', '', content)
content = re.sub(r'\t\(via\s.*?\)\n', '', content)
content = re.sub(r'\t\(zone\s.*?\n(?:\t\t.*\n)*?\t\)\n', '', content)
content = re.sub(r'\t\(gr_line[^)]*\(layer "Edge\.Cuts"\).*?\)\n', '', content)
content = re.sub(r'\t\(gr_arc[^)]*\(layer "Edge\.Cuts"\).*?\)\n', '', content)
content = re.sub(r'\t\(gr_rect[^)]*\(layer "Edge\.Cuts"\).*?\)\n', '', content)
content = re.sub(r'\t\(gr_text\s"[^"]*".*?\)\)\n', '', content, flags=re.DOTALL)

# ============================================================
# Board: 38 x 24mm at (100, 80), rounded corners r=1mm
# ============================================================
ox, oy = 100, 80
bw, bh = 38, 24
r = 1.0  # corner radius

def arc_mid(cx, cy, r, start_angle, end_angle):
    """Midpoint of arc for KiCad (mid-point between start and end on the arc)."""
    mid_angle = (start_angle + end_angle) / 2
    return (cx + r * math.cos(math.radians(mid_angle)),
            cy + r * math.sin(math.radians(mid_angle)))

# Corners: TL, TR, BR, BL
# Each corner: (center_x, center_y, start_angle, end_angle)
corners = {
    'TL': (ox+r,    oy+r,    180, 270),  # top-left
    'TR': (ox+bw-r, oy+r,    270, 360),  # top-right
    'BR': (ox+bw-r, oy+bh-r, 0,   90),   # bottom-right
    'BL': (ox+r,    oy+bh-r, 90,  180),  # bottom-left
}

uid_n = 0xee01
outline = ""

def arc_point(cx, cy, r, angle_deg):
    return (round(cx + r * math.cos(math.radians(angle_deg)), 4),
            round(cy + r * math.sin(math.radians(angle_deg)), 4))

# Top edge: from TL arc end to TR arc start
p1 = arc_point(ox+r, oy+r, r, 270)      # (ox+r, oy)
p2 = arc_point(ox+bw-r, oy+r, r, 270)   # (ox+bw-r, oy)
outline += f'\t(gr_line (start {p1[0]} {p1[1]}) (end {p2[0]} {p2[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid_n:08x}-0000-0000-0000-000000000001"))\n'
uid_n += 1

# TR corner arc
s = arc_point(ox+bw-r, oy+r, r, 270)
e = arc_point(ox+bw-r, oy+r, r, 360)
m = arc_mid(ox+bw-r, oy+r, r, 270, 360)
outline += f'\t(gr_arc (start {s[0]} {s[1]}) (mid {round(m[0],4)} {round(m[1],4)}) (end {e[0]} {e[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid_n:08x}-0000-0000-0000-000000000001"))\n'
uid_n += 1

# Right edge
p1 = arc_point(ox+bw-r, oy+r, r, 0)      # (ox+bw, oy+r)
p2 = arc_point(ox+bw-r, oy+bh-r, r, 0)   # (ox+bw, oy+bh-r)
outline += f'\t(gr_line (start {p1[0]} {p1[1]}) (end {p2[0]} {p2[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid_n:08x}-0000-0000-0000-000000000001"))\n'
uid_n += 1

# BR corner arc
s = arc_point(ox+bw-r, oy+bh-r, r, 0)
e = arc_point(ox+bw-r, oy+bh-r, r, 90)
m = arc_mid(ox+bw-r, oy+bh-r, r, 0, 90)
outline += f'\t(gr_arc (start {s[0]} {s[1]}) (mid {round(m[0],4)} {round(m[1],4)}) (end {e[0]} {e[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid_n:08x}-0000-0000-0000-000000000001"))\n'
uid_n += 1

# Bottom edge
p1 = arc_point(ox+bw-r, oy+bh-r, r, 90)  # (ox+bw-r, oy+bh)
p2 = arc_point(ox+r, oy+bh-r, r, 90)     # (ox+r, oy+bh)
outline += f'\t(gr_line (start {p1[0]} {p1[1]}) (end {p2[0]} {p2[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid_n:08x}-0000-0000-0000-000000000001"))\n'
uid_n += 1

# BL corner arc
s = arc_point(ox+r, oy+bh-r, r, 90)
e = arc_point(ox+r, oy+bh-r, r, 180)
m = arc_mid(ox+r, oy+bh-r, r, 90, 180)
outline += f'\t(gr_arc (start {s[0]} {s[1]}) (mid {round(m[0],4)} {round(m[1],4)}) (end {e[0]} {e[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid_n:08x}-0000-0000-0000-000000000001"))\n'
uid_n += 1

# Left edge
p1 = arc_point(ox+r, oy+bh-r, r, 180)    # (ox, oy+bh-r)
p2 = arc_point(ox+r, oy+r, r, 180)        # (ox, oy+r)
outline += f'\t(gr_line (start {p1[0]} {p1[1]}) (end {p2[0]} {p2[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid_n:08x}-0000-0000-0000-000000000001"))\n'
uid_n += 1

# TL corner arc
s = arc_point(ox+r, oy+r, r, 180)
e = arc_point(ox+r, oy+r, r, 270)
m = arc_mid(ox+r, oy+r, r, 180, 270)
outline += f'\t(gr_arc (start {s[0]} {s[1]}) (mid {round(m[0],4)} {round(m[1],4)}) (end {e[0]} {e[1]}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{uid_n:08x}-0000-0000-0000-000000000001"))\n'
uid_n += 1

# ============================================================
# Component positions v3
# ============================================================
# All passives HORIZONTAL (rot=0) to avoid courtyard surprises
# More spacing between everything
#
# Board interior: x=101 to 137, y=81 to 103
#
# ROW 1 (y=85-89): ICs and big components
# ROW 2 (y=93-96): Passives — each near its parent IC
# ROW 3 (y=101):   Solder pads

positions = {
    # === CHARGER (x=102-114) ===
    "charger.c_in":    (103.0, 84.5, 0),    # C6 — input cap, above U2 left
    "charger.ic":      (107.5, 88.0, 0),     # U2 — TP4056
    "charger.c_bat":   (112.5, 84.5, 0),     # C5 — bat cap, above U2 right
    "charger.r_prog":  (103.0, 94.5, 0),     # R5 — PROG resistor, row 2

    # === MOSFET SWITCH (x=114-120) ===
    "power_sw.mosfet": (117.0, 87.0, 0),     # Q1 — AO3401A
    "power_sw.r_pu":   (117.0, 94.5, 0),     # R8 — pull-up, row 2

    # === BOOST (x=120-137) ===
    "boost.l1":        (123.0, 87.0, 0),     # L1 — 4x4mm inductor
    "boost.ic":        (128.5, 87.0, 0),     # U1 — SX1308
    "boost.d1":        (134.0, 87.0, 0),     # D1 — SS34 diode
    "boost.c_in":      (121.0, 94.5, 0),     # C1 — 10µF, under L1
    "boost.r_fb_top":  (125.0, 94.5, 0),     # R3 — 220k, 4mm gap
    "boost.r_fb_bot":  (129.0, 94.5, 0),     # R2 — 30k, 4mm gap
    "boost.c_out":     (133.5, 94.5, 0),     # C2 — 22µF (0805), under D1
}

# Pads — bottom row, 6mm spacing
pad_positions = {
    "pad_vusb":     (103.0, 101.5),
    "pad_gnd":      (109.0, 101.5),
    "pad_vbat":     (115.0, 101.5),
    "pad_pi_en":    (121.0, 101.5),
    "pad_v5_pi":    (127.0, 101.5),
    "pad_chg_stat": (133.0, 101.5),
}

def move_footprint(content, ato_addr, x, y, rot=0):
    idx = content.find(f'atopile_address" "{ato_addr}"')
    if idx == -1:
        print(f"  NOT FOUND: {ato_addr}")
        return content
    fp_start = content.rfind('(footprint ', 0, idx)
    if fp_start == -1:
        return content
    block_end = min(fp_start + 400, len(content))
    block = content[fp_start:block_end]
    at_match = re.search(r'\(at [\d\.]+ [\d\.]+(?: [\d]+)?\)', block)
    if not at_match:
        return content
    old_at = at_match.group(0)
    rot_str = f' {rot}' if rot else ''
    new_at = f'(at {x} {y}{rot_str})'
    new_block = block.replace(old_at, new_at, 1)
    content = content[:fp_start] + new_block + content[block_end:]
    print(f"  {ato_addr:20s} -> ({x}, {y}, {rot}°)")
    return content

print("Placing components:")
for addr, pos in positions.items():
    content = move_footprint(content, addr, pos[0], pos[1], pos[2])

print("\nPlacing pads:")
for addr, (x, y) in pad_positions.items():
    content = move_footprint(content, addr, x, y)

# ============================================================
# Silkscreen labels for pads
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
uid_n = 0xff01
for text, x, y in pad_labels:
    silkscreen += f'\t(gr_text "{text}" (at {x} {y}) (layer "F.SilkS") (uuid "{uid_n:08x}-0000-0000-0000-000000000001")\n'
    silkscreen += f'\t\t(effects (font (size 0.7 0.7) (thickness 0.12)) (justify bottom))\n\t)\n'
    uid_n += 1

# Board title
silkscreen += f'\t(gr_text "NW-PWR" (at 104 82) (layer "F.SilkS") (uuid "ff000010-0000-0000-0000-000000000001")\n'
silkscreen += f'\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))\n\t)\n'

# ============================================================
# GND pour on B.Cu (rectangular, inside rounded board)
# ============================================================
gnd_zone = f"""
\t(zone (net 15) (net_name "lv") (layer "B.Cu") (uuid "dd000001-0000-0000-0000-000000000002") (hatch edge 0.5)
\t\t(connect_pads (clearance 0.3))
\t\t(min_thickness 0.2) (filled_areas_thickness no)
\t\t(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy {ox+0.5} {oy+0.5})
\t\t\t\t(xy {ox+bw-0.5} {oy+0.5})
\t\t\t\t(xy {ox+bw-0.5} {oy+bh-0.5})
\t\t\t\t(xy {ox+0.5} {oy+bh-0.5})
\t\t\t)
\t\t)
\t)
"""

# Insert before closing paren
content = content.rstrip()
if content.endswith(')'):
    content = content[:-1] + outline + silkscreen + gnd_zone + ')\n'

with open(PCB_PATH, 'w') as f:
    f.write(content)

print(f"\nDone! {bw}x{bh}mm board with {r}mm rounded corners")
