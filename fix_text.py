#!/usr/bin/env python3
"""Fix reference text positions and hide value labels to prevent overlap."""
import re

PCB = "layouts/default/default.kicad_pcb"
with open(PCB) as f:
    content = f.read()

# Remove duplicate NW-PWR silkscreen text if any
# Count and remove all gr_text "NW-PWR" entries
nw_count = content.count('gr_text "NW-PWR')
if nw_count > 0:
    content = re.sub(r'\t\(gr_text "NW-PWR[^"]*".*?\)\)\n', '', content, flags=re.DOTALL)
    print(f"Removed {nw_count} NW-PWR text(s)")

# Add single NW-PWR at bottom-right corner (away from components)
uid = "ff100001-0000-0000-0000-000000000001"
nwpwr = f'\t(gr_text "NW-PWR" (at 134 102.5) (layer "F.SilkS") (uuid "{uid}")\n'
nwpwr += f'\t\t(effects (font (size 0.7 0.7) (thickness 0.12)))\n\t)\n'

# Reference text offset overrides (relative to footprint center)
# Goal: put ref designator to the SIDE of the component, not above/below
ref_overrides = {
    # Charger: C6 and C5 are at y=84.5, put text to right/left instead of above
    "charger.ic":      {"ref": (0, -4.5), "val_hide": True},      # U2 — above, but less
    "charger.c_in":    {"ref": (3.5, 0), "val_hide": True},       # C6 — text to right
    "charger.c_bat":   {"ref": (3.5, 0), "val_hide": True},       # C5 — text to right
    "charger.r_prog":  {"ref": (3, 0), "val_hide": True},         # R5 — text to right
    
    "power_sw.mosfet": {"ref": (0, -3.5), "val_hide": True},      # Q1 — above
    "power_sw.r_pu":   {"ref": (3, 0), "val_hide": True},         # R8 — right
    
    "boost.l1":        {"ref": (0, -3.5), "val_hide": True},      # L1 — above
    "boost.ic":        {"ref": (0, -3), "val_hide": True},         # U1 — above
    "boost.d1":        {"ref": (0, -3), "val_hide": True},         # D1 — above
    "boost.c_in":      {"ref": (3.5, 0), "val_hide": True},       # C1 — right
    "boost.r_fb_top":  {"ref": (3, 0), "val_hide": True},         # R3 — right
    "boost.r_fb_bot":  {"ref": (3, 0), "val_hide": True},         # R2 — right
    "boost.c_out":     {"ref": (3.5, 0), "val_hide": True},       # C2 — right
    
    # Pads: hide all text
    "pad_vusb":     {"ref_hide": True, "val_hide": True},
    "pad_gnd":      {"ref_hide": True, "val_hide": True},
    "pad_vbat":     {"ref_hide": True, "val_hide": True},
    "pad_v5_pi":    {"ref_hide": True, "val_hide": True},
    "pad_pi_en":    {"ref_hide": True, "val_hide": True},
    "pad_chg_stat": {"ref_hide": True, "val_hide": True},
}

for ato_addr, overrides in ref_overrides.items():
    idx = content.find(f'atopile_address" "{ato_addr}"')
    if idx == -1:
        print(f"  NOT FOUND: {ato_addr}")
        continue
    
    fp_start = content.rfind('(footprint ', 0, idx)
    # Find next footprint or end
    fp_end = content.find('\n\t(footprint ', fp_start + 1)
    if fp_end == -1:
        fp_end = len(content)
    
    block = content[fp_start:fp_end]
    new_block = block
    
    # Fix Reference text position
    if "ref" in overrides:
        rx, ry = overrides["ref"]
        ref_pattern = r'(property "Reference".*?\(at )([\d\.\-]+) ([\d\.\-]+)'
        ref_match = re.search(ref_pattern, new_block, re.DOTALL)
        if ref_match:
            old = ref_match.group(0)
            new = f'{ref_match.group(1)}{rx} {ry}'
            new_block = new_block.replace(old, new, 1)
    
    # Hide reference text
    if overrides.get("ref_hide"):
        # Add hide to effects if not present
        ref_section = re.search(r'(property "Reference".*?)(effects \(font)', new_block, re.DOTALL)
        if ref_section and 'hide' not in ref_section.group(0):
            old = ref_section.group(2)
            new_block = new_block.replace(old, f'effects hide (font', 1)
    
    # Hide Value text
    if overrides.get("val_hide"):
        val_section = re.search(r'(property "Value".*?)(effects \(font)', new_block, re.DOTALL)
        if val_section and 'hide' not in val_section.group(0):
            old = val_section.group(2)
            new_block = new_block.replace(old, f'effects hide (font', 1)
    
    if new_block != block:
        content = content[:fp_start] + new_block + content[fp_end:]
        print(f"  Fixed {ato_addr}")

# Insert NW-PWR text before closing paren
content = content.rstrip()
if content.endswith(')'):
    content = content[:-1] + nwpwr + ')\n'

with open(PCB, 'w') as f:
    f.write(content)

print("\nDone! Reference text repositioned, values hidden, NW-PWR moved to corner")
