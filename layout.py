#!/usr/bin/env python3
"""
NumWorks N0100 Power Board — PCB Layout Script
Edits layouts/default/default.kicad_pcb to position components,
add board outline, silkscreen, design rules, traces, and ground pour.
"""

import re
import uuid
import math

PCB_FILE = "layouts/default/default.kicad_pcb"

def gen_uuid():
    return str(uuid.uuid4())

def read_pcb():
    with open(PCB_FILE, "r") as f:
        return f.read()

def write_pcb(content):
    with open(PCB_FILE, "w") as f:
        f.write(content)

# ============================================================
# Component positions — all coordinates are ABSOLUTE (mm)
# Board origin: (100, 80), size: 30×18mm
# ============================================================

# Board params
BX, BY = 100, 80  # board origin (top-left)
BW, BH = 30, 18   # board size

POSITIONS = {
    # === Left zone: Charger (TP4056) ===
    # TP4056 is ESOP-8 with pins on top/bottom, EP center
    # Pin 1 (GND) at bottom-left, Pin 8 (VCC) at top-left
    "charger.ic":       (BX + 5,   BY + 8.5, 0),    # U2 — center of left zone
    "charger.c_in":     (BX + 9,   BY + 5,   0),    # C6 — USB input cap, near VCC pin
    "charger.c_bat":    (BX + 9,   BY + 12,  0),    # C5 — battery cap, near BAT pin
    "charger.r_prog":   (BX + 1.5, BY + 11,  0),    # R5 — PROG resistor, near PROG pin

    # === Center zone: MOSFET switch ===
    "power_sw.mosfet":  (BX + 13,  BY + 8.5, 0),    # Q1
    "power_sw.r_pu":    (BX + 13,  BY + 5.5, 0),    # R8 — pull-up to VBAT

    # === Right zone: Boost converter (SX1308) ===
    "boost.ic":         (BX + 21,  BY + 9,   0),    # U1 — SX1308
    "boost.l1":         (BX + 17,  BY + 9,   0),    # L1 — inductor, close to VIN/SW
    "boost.d1":         (BX + 24.5, BY + 6,  0),    # D1 — SS34 diode, SW→VOUT
    "boost.r_fb_top":   (BX + 24.5, BY + 11, 90),   # R3 — 220kΩ FB top
    "boost.r_fb_bot":   (BX + 24.5, BY + 13, 90),   # R2 — 30kΩ FB bottom
    "boost.c_in":       (BX + 17,  BY + 5,   0),    # C1 — 10µF input cap
    "boost.c_out":      (BX + 28,  BY + 9,   0),    # C2 — 22µF output cap

    # === Solder pads — along bottom edge ===
    "pad_vusb":         (BX + 3,   BY + 16.5, 0),   # J6 — VUSB
    "pad_gnd":          (BX + 8,   BY + 16.5, 0),   # J2 — GND
    "pad_vbat":         (BX + 13,  BY + 16.5, 0),   # J5 — VBAT
    "pad_pi_en":        (BX + 18,  BY + 16.5, 0),   # J3 — PI_EN
    "pad_v5_pi":        (BX + 23,  BY + 16.5, 0),   # J4 — V5_PI
    "pad_chg_stat":     (BX + 28,  BY + 16.5, 0),   # J1 — CHG_STAT
}


def set_footprint_position(pcb, atopile_addr, x, y, angle):
    """Find footprint by atopile_address and set its position."""
    # Find the footprint block containing this atopile_address
    pattern = rf'(property "atopile_address" "{re.escape(atopile_addr)}")'
    
    if not re.search(pattern, pcb):
        print(f"  WARNING: atopile_address '{atopile_addr}' not found!")
        return pcb
    
    # Find the footprint containing this address and update its (at X Y) or (at X Y angle)
    # Strategy: find the footprint start, then update the (at ...) line
    
    # Split into footprint blocks
    result = []
    i = 0
    lines = pcb.split('\n')
    in_target_fp = False
    fp_depth = 0
    found_at = False
    
    for idx, line in enumerate(lines):
        if f'atopile_address" "{atopile_addr}"' in line:
            # We're inside the target footprint, need to find its (at ...) which is near the start
            in_target_fp = True
        result.append(line)
    
    # Different approach: use regex on the whole text
    # Find footprint block by atopile_address, then update the (at ...) near the beginning
    
    # Find all footprint blocks
    fp_pattern = re.compile(
        r'(\(footprint\s+"[^"]*"\s*\n\s*\(layer "[^"]*"\)\s*\n\s*\(uuid "[^"]*"\)\s*\n\s*)\(at\s+[\d.\-]+\s+[\d.\-]+(?:\s+[\d.\-]+)?\)',
        re.MULTILINE
    )
    
    def replace_at(match):
        prefix = match.group(0)
        # Check if this footprint contains our atopile_address
        # Find the end of this footprint block
        start = match.start()
        # Look ahead for our address
        search_end = min(start + 5000, len(pcb))
        chunk = pcb[start:search_end]
        if f'atopile_address" "{atopile_addr}"' in chunk:
            # Replace the (at ...) part
            at_str = f"(at {x} {y})" if angle == 0 else f"(at {x} {y} {angle})"
            new = re.sub(r'\(at\s+[\d.\-]+\s+[\d.\-]+(?:\s+[\d.\-]+)?\)', at_str, match.group(0))
            return new
        return match.group(0)
    
    pcb = fp_pattern.sub(replace_at, pcb)
    return pcb


def remove_old_edge_cuts(pcb):
    """Remove all existing Edge.Cuts lines."""
    pcb = re.sub(r'\t\(gr_line\s*\n\s*\(start[^)]*\)\s*\n\s*\(end[^)]*\)\s*\n\s*\(stroke[^)]*\(width[^)]*\)\s*\n\s*\(type[^)]*\)\s*\n\s*\)\s*\n\s*\(layer "Edge\.Cuts"\)\s*\n\s*\)', '', pcb)
    # Simpler: remove any gr_line on Edge.Cuts
    lines = pcb.split('\n')
    result = []
    skip_until_close = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'gr_line' in line or 'gr_arc' in line:
            # Look ahead for Edge.Cuts
            block = []
            j = i
            depth = 0
            while j < len(lines):
                block.append(lines[j])
                depth += lines[j].count('(') - lines[j].count(')')
                if depth <= 0:
                    break
                j += 1
            block_text = '\n'.join(block)
            if 'Edge.Cuts' in block_text:
                i = j + 1
                continue
        result.append(line)
        i += 1
    return '\n'.join(result)


def add_board_outline(pcb):
    """Add 30×18mm board outline with rounded corners on Edge.Cuts."""
    x1, y1 = BX, BY
    x2, y2 = BX + BW, BY + BH
    r = 0.5  # corner radius
    
    outline = f"""
\t(gr_line (start {x1 + r} {y1}) (end {x2 - r} {y1}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))
\t(gr_line (start {x2} {y1 + r}) (end {x2} {y2 - r}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))
\t(gr_line (start {x2 - r} {y2}) (end {x1 + r} {y2}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))
\t(gr_line (start {x1} {y2 - r}) (end {x1} {y1 + r}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))
\t(gr_arc (start {x1 + r} {y1}) (mid {x1 + r - r*math.cos(math.pi/4)} {y1 + r - r*math.sin(math.pi/4)}) (end {x1} {y1 + r}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))
\t(gr_arc (start {x2} {y1 + r}) (mid {x2 - r + r*math.cos(math.pi/4)} {y1 + r - r*math.sin(math.pi/4)}) (end {x2 - r} {y1}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))
\t(gr_arc (start {x2 - r} {y2}) (mid {x2 - r + r*math.cos(math.pi/4)} {y2 - r + r*math.sin(math.pi/4)}) (end {x2} {y2 - r}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))
\t(gr_arc (start {x1} {y2 - r}) (mid {x1 + r - r*math.cos(math.pi/4)} {y2 - r + r*math.sin(math.pi/4)}) (end {x1 + r} {y2}) (stroke (width 0.1) (type solid)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))"""
    
    return outline


def add_silkscreen_labels():
    """Add silkscreen text labels for pads and board title."""
    labels = []
    
    # Board title
    labels.append(f'\t(gr_text "NW-PWR" (at {BX + 15} {BY + 2}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.2 1.2) (thickness 0.15))))')
    
    # Pad labels — positioned above each pad (lower Y = above)
    pad_labels = {
        "pad_vusb":     ("VUSB",     BX + 3,   BY + 14.5),
        "pad_gnd":      ("GND",      BX + 8,   BY + 14.5),
        "pad_vbat":     ("VBAT",     BX + 13,  BY + 14.5),
        "pad_pi_en":    ("PI_EN",    BX + 18,  BY + 14.5),
        "pad_v5_pi":    ("V5_PI",    BX + 23,  BY + 14.5),
        "pad_chg_stat": ("CHG",      BX + 28,  BY + 14.5),
    }
    
    for addr, (text, x, y) in pad_labels.items():
        labels.append(f'\t(gr_text "{text}" (at {x} {y}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    
    return '\n'.join(labels)


def add_design_rules(pcb):
    """Update design rules in the setup section."""
    # Add design rules after the pcbplotparams section
    rules = """
\t\t(defaults
\t\t\t(min_clearance 0.2)
\t\t\t(min_track_width 0.2)
\t\t\t(min_via_annulus 0.15)
\t\t\t(min_via_diameter 0.6)
\t\t)"""
    
    # Insert before the closing ) of setup
    # Actually, let's add net classes for power vs signal traces
    return pcb


def add_traces_and_zones(pcb):
    """Add copper traces and ground zone."""
    traces = []
    
    # Net numbers (from the PCB file):
    # 1 = c_out-power-hv (V5_PI)
    # 2 = "2" (SW node)
    # 3 = c_in-power-hv (VUSB)
    # 4 = FB
    # 5 = hv (vbat_switched)
    # 6 = chg_stat
    # 7 = c_bat-power-hv (VBAT)
    # 8 = pi_en
    # 9 = PROG
    # 10 = nSTDBY
    # 15 = lv (GND)
    
    NET_GND = 15
    NET_VUSB = 3
    NET_VBAT = 7
    NET_V5PI = 1
    NET_VBATSW = 5
    NET_SW = 2
    NET_FB = 4
    NET_PROG = 9
    NET_PIEN = 8
    NET_CHGSTAT = 6
    NET_NSTDBY = 10
    
    PW = 0.5   # power trace width
    SW = 0.25  # signal trace width
    
    # Component pad positions (absolute, based on footprint position + pad offset)
    # These are calculated from the footprint positions and pad offsets in the kicad_pcb
    
    # TP4056 (U2) at (105, 88.5), ESOP-8 pads:
    # Pin 1 (GND): (-1.91, +2.91) = (103.09, 91.41)
    # Pin 2 (PROG): (-0.64, +2.91) = (104.36, 91.41)
    # Pin 3 (GND): (+0.64, +2.91) = (105.64, 91.41)
    # Pin 4 (VCC/VUSB): (+1.91, +2.91) = (106.91, 91.41)
    # Pin 5 (BAT): (+1.91, -2.91) = (106.91, 85.59)
    # Pin 6 (nSTDBY): (+0.64, -2.91) = (105.64, 85.59)
    # Pin 7 (nCHRG/chg_stat): (-0.64, -2.91) = (104.36, 85.59)
    # Pin 8 (VCC/VUSB): (-1.91, -2.91) = (103.09, 85.59)
    # Pin 9 (EP/GND): (0, 0) = (105, 88.5)
    U2 = {
        1: (103.09, 91.41),  # GND
        2: (104.36, 91.41),  # PROG
        3: (105.64, 91.41),  # GND
        4: (106.91, 91.41),  # VCC (VUSB)
        5: (106.91, 85.59),  # BAT (VBAT)
        6: (105.64, 85.59),  # nSTDBY
        7: (104.36, 85.59),  # nCHRG (chg_stat)
        8: (103.09, 85.59),  # VCC (VUSB)
        9: (105.0,  88.5),   # EP (GND)
    }
    
    # SX1308 (U1) at (121, 89), SOT-23-6 pads:
    # Pin 1 (SW): (-0.95, +1.15) = (120.05, 90.15)
    # Pin 2 (GND): (0, +1.15) = (121, 90.15)
    # Pin 3 (FB): (+0.95, +1.15) = (121.95, 90.15)
    # Pin 4 (EN): (+0.95, -1.15) = (121.95, 87.85)
    # Pin 5 (VIN): (0, -1.15) = (121, 87.85)
    # Pin 6 (NC): (-0.95, -1.15) = (120.05, 87.85)
    U1 = {
        1: (120.05, 90.15),  # SW
        2: (121.0,  90.15),  # GND
        3: (121.95, 90.15),  # FB
        4: (121.95, 87.85),  # EN (= vbat_switched)
        5: (121.0,  87.85),  # VIN (= vbat_switched)
        6: (120.05, 87.85),  # NC
    }
    
    # L1 inductor at (117, 89), pads at ±1.8
    L1 = {
        1: (115.2, 89.0),  # VIN side (= vbat_switched)
        2: (118.8, 89.0),  # SW side
    }
    
    # D1 SS34 diode at (124.5, 86), pads at ±2.2 (anode=A=pin2, cathode=K=pin1)
    # Wait, from PCB: pad "2" net "2" (SW), pad "1" net c_out-power-hv (V5_PI)
    # But the atopile code says d1.A ~ ic.SW (anode=SW node), d1.K ~ vout (cathode=V5_PI)
    # In the footprint: pad 1 at -2.2 = anode (left), pad 2 at +2.2 = cathode (right)
    # Actually re-reading: pad "2" has net "2" (SW) → this is ANODE
    # pad "1" has net c_out-power-hv (V5_PI) → this is CATHODE
    # Hmm the pad numbering in the footprint maps A→pad2, K→pad1 
    D1 = {
        1: (122.3, 86.0),  # Cathode (V5_PI) — at -2.2 from center
        2: (126.7, 86.0),  # Anode (SW) — at +2.2 from center
    }
    
    # Q1 AO3401A at (113, 88.5), SOT-23 pads
    # Pin 1 (G): (+1.15, +0.95) = (114.15, 89.45)  -- with 180° rotation offsets flip
    # Pin 2 (S): (+1.15, -0.95) = (114.15, 87.55)
    # Pin 3 (D): (-1.15, 0) = (111.85, 88.5)
    Q1 = {
        1: (114.15, 89.45),  # G (pi_en)
        2: (114.15, 87.55),  # S (VBAT)
        3: (111.85, 88.5),   # D (vbat_switched)
    }
    
    # R8 at (113, 85.5), 0402 vertical (90°)
    # Pad 1 at -0.43 offset → rotated 90° → (113, 85.07) — VBAT
    # Pad 2 at +0.43 offset → rotated 90° → (113, 85.93) — pi_en
    R8 = {
        1: (113.0, 85.07),  # VBAT
        2: (113.0, 85.93),  # pi_en
    }
    
    # R5 at (101.5, 91), 0402 vertical
    R5 = {
        1: (101.5, 90.57),  # PROG
        2: (101.5, 91.43),  # GND
    }
    
    # C6 (charger.c_in) at (109, 85), 0603 horizontal
    C6 = {
        1: (108.3, 85.0),   # VUSB
        2: (109.7, 85.0),   # GND
    }
    
    # C5 (charger.c_bat) at (109, 92), 0603 horizontal
    C5 = {
        1: (108.3, 92.0),   # VBAT
        2: (109.7, 92.0),   # GND
    }
    
    # R3 (boost.r_fb_top) at (124.5, 91), 0603 vertical (90°)
    R3 = {
        1: (124.5, 90.25),  # V5_PI
        2: (124.5, 91.75),  # FB
    }
    
    # R2 (boost.r_fb_bot) at (124.5, 93), 0603 vertical (90°)
    R2 = {
        1: (124.5, 92.25),  # FB
        2: (124.5, 93.75),  # GND
    }
    
    # C1 (boost.c_in) at (117, 85), 0603 horizontal
    C1 = {
        1: (116.3, 85.0),   # vbat_switched
        2: (117.7, 85.0),   # GND
    }
    
    # C2 (boost.c_out) at (128, 89), 0805 horizontal
    C2 = {
        1: (127.0, 89.0),   # V5_PI
        2: (129.0, 89.0),   # GND
    }
    
    # Solder pads (all at y=96.5, single pad at center)
    PAD_VUSB =     (103.0, 96.5)
    PAD_GND =      (108.0, 96.5)
    PAD_VBAT =     (113.0, 96.5)
    PAD_PIEN =     (118.0, 96.5)
    PAD_V5PI =     (123.0, 96.5)
    PAD_CHGSTAT =  (128.0, 96.5)
    
    def seg(x1, y1, x2, y2, width, net, layer="F.Cu"):
        return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {width}) (layer "{layer}") (net {net}) (uuid "{gen_uuid()}"))'
    
    def via(x, y, net):
        return f'\t(via (at {x} {y}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{gen_uuid()}"))'
    
    # ====================================================================
    # ROUTING
    # ====================================================================
    
    # --- VUSB net (3) ---
    # Pad VUSB → up → U2 pin 4 (VCC)
    traces.append(seg(PAD_VUSB[0], PAD_VUSB[1], PAD_VUSB[0], U2[4][1], PW, NET_VUSB))
    traces.append(seg(PAD_VUSB[0], U2[4][1], U2[4][0], U2[4][1], PW, NET_VUSB))
    # U2 pin 8 (VCC) to pin 4 — via the top 
    traces.append(seg(U2[8][0], U2[8][1], U2[8][0], 84.5, PW, NET_VUSB))
    traces.append(seg(U2[8][0], 84.5, U2[4][0], 84.5, PW, NET_VUSB))
    traces.append(seg(U2[4][0], 84.5, U2[4][0], U2[4][1], PW, NET_VUSB))
    # C6 (charger.c_in) pin 1 to VUSB net
    traces.append(seg(C6[1][0], C6[1][1], U2[8][0], C6[1][1], PW, NET_VUSB))
    traces.append(seg(U2[8][0], C6[1][1], U2[8][0], U2[8][1], PW, NET_VUSB))
    
    # --- VBAT net (7) ---
    # U2 pin 5 (BAT) → C5 pin 1
    traces.append(seg(U2[5][0], U2[5][1], C5[1][0], U2[5][1], PW, NET_VBAT))
    traces.append(seg(C5[1][0], U2[5][1], C5[1][0], C5[1][1], PW, NET_VBAT))
    # Q1 pin 2 (Source=VBAT) → R8 pin 1
    traces.append(seg(Q1[2][0], Q1[2][1], R8[1][0], Q1[2][1], PW, NET_VBAT))
    traces.append(seg(R8[1][0], Q1[2][1], R8[1][0], R8[1][1], PW, NET_VBAT))
    # VBAT pad → up to Q1 area
    traces.append(seg(PAD_VBAT[0], PAD_VBAT[1], PAD_VBAT[0], Q1[2][1], PW, NET_VBAT))
    traces.append(seg(PAD_VBAT[0], Q1[2][1], Q1[2][0], Q1[2][1], PW, NET_VBAT))
    # Connect C5 side to Q1 source
    traces.append(seg(C5[1][0], U2[5][1], R8[1][0], U2[5][1], PW, NET_VBAT))
    
    # --- vbat_switched net (5) ---
    # Q1 drain → L1 pin 1
    traces.append(seg(Q1[3][0], Q1[3][1], L1[1][0], Q1[3][1], PW, NET_VBATSW))
    traces.append(seg(L1[1][0], Q1[3][1], L1[1][0], L1[1][1], PW, NET_VBATSW))
    # L1 pin 1 → C1 pin 1 (boost input cap)
    traces.append(seg(L1[1][0], L1[1][1], C1[1][0], L1[1][1], PW, NET_VBATSW))
    traces.append(seg(C1[1][0], L1[1][1], C1[1][0], C1[1][1], PW, NET_VBATSW))
    # U1 pin 4 (EN) and pin 5 (VIN) — both are vbat_switched
    traces.append(seg(U1[5][0], U1[5][1], U1[5][0], 87.0, PW, NET_VBATSW))
    traces.append(seg(U1[5][0], 87.0, L1[1][0], 87.0, PW, NET_VBATSW))
    traces.append(seg(L1[1][0], 87.0, L1[1][0], L1[1][1], PW, NET_VBATSW))
    traces.append(seg(U1[4][0], U1[4][1], U1[5][0], U1[4][1], PW, NET_VBATSW))
    
    # --- SW node net (2) ---
    # L1 pin 2 → U1 pin 1 (SW)
    traces.append(seg(L1[2][0], L1[2][1], U1[1][0], L1[2][1], PW, NET_SW))
    traces.append(seg(U1[1][0], L1[2][1], U1[1][0], U1[1][1], PW, NET_SW))
    # D1 pin 2 (Anode=SW) — connect to SW node
    # Route: U1 pin 1 → up → D1 anode
    traces.append(seg(U1[1][0], U1[1][1], U1[1][0], 91.0, PW, NET_SW))
    traces.append(seg(U1[1][0], 91.0, D1[2][0], 91.0, PW, NET_SW))
    traces.append(seg(D1[2][0], 91.0, D1[2][0], D1[2][1], PW, NET_SW))
    
    # --- V5_PI net (1) ---
    # D1 pin 1 (Cathode=V5_PI) → C2 pin 1 (output cap)
    traces.append(seg(D1[1][0], D1[1][1], D1[1][0], C2[1][1], PW, NET_V5PI))
    traces.append(seg(D1[1][0], C2[1][1], C2[1][0], C2[1][1], PW, NET_V5PI))
    # R3 pin 1 → V5_PI
    traces.append(seg(R3[1][0], R3[1][1], C2[1][0], R3[1][1], PW, NET_V5PI))
    traces.append(seg(C2[1][0], R3[1][1], C2[1][0], C2[1][1], PW, NET_V5PI))
    # V5_PI pad → up
    traces.append(seg(PAD_V5PI[0], PAD_V5PI[1], PAD_V5PI[0], C2[1][1], PW, NET_V5PI))
    traces.append(seg(PAD_V5PI[0], C2[1][1], C2[1][0], C2[1][1], PW, NET_V5PI))
    
    # --- FB net (4) ---
    # R3 pin 2 → R2 pin 1 (series divider)
    traces.append(seg(R3[2][0], R3[2][1], R2[1][0], R2[1][1], SW, NET_FB))
    # U1 pin 3 (FB) → R3/R2 junction
    traces.append(seg(U1[3][0], U1[3][1], R3[2][0], U1[3][1], SW, NET_FB))
    traces.append(seg(R3[2][0], U1[3][1], R3[2][0], R3[2][1], SW, NET_FB))
    
    # --- PROG net (9) ---
    # U2 pin 2 → R5 pin 1
    traces.append(seg(U2[2][0], U2[2][1], R5[1][0], U2[2][1], SW, NET_PROG))
    traces.append(seg(R5[1][0], U2[2][1], R5[1][0], R5[1][1], SW, NET_PROG))
    
    # --- pi_en net (8) ---
    # Q1 pin 1 (Gate) → R8 pin 2
    traces.append(seg(Q1[1][0], Q1[1][1], R8[2][0], Q1[1][1], SW, NET_PIEN))
    traces.append(seg(R8[2][0], Q1[1][1], R8[2][0], R8[2][1], SW, NET_PIEN))
    # PI_EN pad → up to Q1 gate
    traces.append(seg(PAD_PIEN[0], PAD_PIEN[1], PAD_PIEN[0], Q1[1][1], SW, NET_PIEN))
    traces.append(seg(PAD_PIEN[0], Q1[1][1], Q1[1][0], Q1[1][1], SW, NET_PIEN))
    
    # --- chg_stat net (6) ---
    # U2 pin 7 → CHG_STAT pad
    traces.append(seg(U2[7][0], U2[7][1], U2[7][0], 84.0, SW, NET_CHGSTAT))
    traces.append(seg(U2[7][0], 84.0, PAD_CHGSTAT[0], 84.0, SW, NET_CHGSTAT))
    traces.append(seg(PAD_CHGSTAT[0], 84.0, PAD_CHGSTAT[0], PAD_CHGSTAT[1], SW, NET_CHGSTAT))
    
    # --- GND connections via vias to back copper pour ---
    # Add vias at key GND points
    gnd_via_points = [
        U2[1],       # U2 pin 1 (GND)
        U2[3],       # U2 pin 3 (GND)
        (U2[9][0], U2[9][1]),  # U2 EP (GND)
        C6[2],       # C6 pin 2 (GND)
        C5[2],       # C5 pin 2 (GND)
        R5[2],       # R5 pin 2 (GND)
        U1[2],       # U1 pin 2 (GND)
        C1[2],       # C1 pin 2 (GND)
        C2[2],       # C2 pin 2 (GND)
        R2[2],       # R2 pin 2 (GND)
        PAD_GND,     # GND pad
    ]
    
    for pt in gnd_via_points:
        traces.append(via(pt[0], pt[1], NET_GND))
    
    # Short GND traces on F.Cu to connect pads to nearby vias
    # U2 EP to pin 1 and pin 3
    traces.append(seg(U2[9][0], U2[9][1], U2[1][0], U2[9][1], PW, NET_GND))
    traces.append(seg(U2[1][0], U2[9][1], U2[1][0], U2[1][1], PW, NET_GND))
    traces.append(seg(U2[9][0], U2[9][1], U2[3][0], U2[9][1], PW, NET_GND))
    traces.append(seg(U2[3][0], U2[9][1], U2[3][0], U2[3][1], PW, NET_GND))
    # GND pad to via
    traces.append(seg(PAD_GND[0], PAD_GND[1], PAD_GND[0], PAD_GND[1], PW, NET_GND))
    
    # ====================================================================
    # GROUND POUR on B.Cu
    # ====================================================================
    zone = f"""
\t(zone (net {NET_GND}) (net_name "lv") (layer "B.Cu") (uuid "{gen_uuid()}")
\t\t(hatch edge 0.5)
\t\t(connect_pads (clearance 0.2))
\t\t(min_thickness 0.2)
\t\t(filled_areas_thickness no)
\t\t(fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))
\t\t(polygon
\t\t\t(pts
\t\t\t\t(xy {BX + 0.3} {BY + 0.3})
\t\t\t\t(xy {BX + BW - 0.3} {BY + 0.3})
\t\t\t\t(xy {BX + BW - 0.3} {BY + BH - 0.3})
\t\t\t\t(xy {BX + 0.3} {BY + BH - 0.3})
\t\t\t)
\t\t)
\t)"""
    
    return '\n'.join(traces) + zone


def main():
    print("Reading PCB file...")
    pcb = read_pcb()
    
    # Step 1: Position all components
    print("Positioning components...")
    for addr, (x, y, angle) in POSITIONS.items():
        pcb = set_footprint_position(pcb, addr, x, y, angle)
        print(f"  {addr} → ({x}, {y}, {angle}°)")
    
    # Step 2: Remove old Edge.Cuts and add new board outline
    print("Updating board outline...")
    pcb = remove_old_edge_cuts(pcb)
    
    # Step 3: Add board outline, silkscreen, traces before the final closing paren
    print("Adding board outline, silkscreen, and traces...")
    outline = add_board_outline(pcb)
    silkscreen = add_silkscreen_labels()
    routing = add_traces_and_zones(pcb)
    
    # Insert before the final closing paren
    pcb = pcb.rstrip()
    if pcb.endswith(')'):
        pcb = pcb[:-1]
    pcb += outline + '\n' + silkscreen + '\n' + routing + '\n)\n'
    
    print("Writing PCB file...")
    write_pcb(pcb)
    print(f"Done! Board: {BW}mm × {BH}mm at ({BX}, {BY})")
    print(f"Components: 13 original + 6 solder pads = 19 total")


if __name__ == "__main__":
    main()
