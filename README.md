# NumWorks N0100 Power Module

Internal daughter board for the NumWorks N0100 calculator:
- **TP4056** Li-Ion charger (replaces broken RT9526A)
- **DW01A + FS8205A** battery protection
- **TPS63020** 5V buck-boost for Raspberry Pi Zero 2W

Built with [atopile](https://atopile.io) — all parts sourced from JLCPCB/LCSC.

## Status
🚧 Work in progress

## Docs
- [Design Spec](docs/design-spec.md) — full circuit design, pin mappings, power budget
- [Tool Learnings](docs/tool-learnings.md) — PCB tool comparison (Zener vs atopile)

## Building
```bash
# Requires atopile v0.14.0+
ato build
```

## Related
- [numworks-rpi](https://github.com/elektricM/numworks-rpi) — firmware, Pi Linux setup, architecture docs
