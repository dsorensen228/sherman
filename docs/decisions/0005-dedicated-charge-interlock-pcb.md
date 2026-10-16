# ADR 0005: Use a Dedicated Charge-Interlock PCB

## Status

Accepted for fabrication and bench qualification on 2026-09-01. Mobile use
remains gated by P3-PWR-001 electrical qualification.

## Context

ADR 0004 requires a retained, automatic, dual-inhibit charge interlock. The
half-size Perma-Proto selected for the first bench layout is approximately
82.6 mm × 45.7 mm and does not fit Sherman's 75 mm × 65 mm target chassis
envelope with the rest of the power and compute stack. The user-facing charging
contract is non-negotiable: insert charging power and take no other action.

## Decision

Use the dedicated `charging-interlock-rev-a` PCB in `electronics/pcb/`. It is a
38.10 mm × 24.13 mm, two-layer, through-hole board that preserves the W1
`CHARGE_ABSENT`, `MOTOR_GATE_CTRL`, and `MOTOR_SLEEP_N` circuit exactly. It uses
the already-selected SN74HC08N, 2N3904BU, axial resistors, ceramic bypass
capacitor, socket, and 2.54 mm harness headers.

This is a single-purpose safety interlock board, not authorization for a custom
Luckfox carrier or a general Sherman motherboard. Its connector labels and
square pin-1 pads are part of the safety design.

## Alternatives

- Retain the Perma-Proto: rejected because its physical area is incompatible
  with the chassis envelope.
- Make an SMD board: deferred. It would be smaller but would discard the parts
  already purchased and make field rework harder without improving V1 charging
  behavior.
- Fold the circuit into a future carrier: rejected for V1 because it broadens
  scope and couples interlock qualification to unrelated interfaces.

## Consequences

- The interlock footprint area drops by about 76 percent.
- Two identical populated boards can be assembled and truth-table tested, one
  installed and one held as a known-good spare.
- Vertical resistors keep the board small but require controlled lead forming
  and inspection.
- Bare-board fabrication can proceed before power-tree release, but mobile
  installation cannot.

## Verification

- Regenerate the board and pass `electronics.tests.test_charging_interlock_pcb`.
- Independently parse the Gerber ZIP as two copper layers, two masks, front
  legend, profile, PTH drill, and NPTH drill.
- Build and test two boards with the Section 10 truth table, including raw VBUS,
  `PGOOD`, Pico reset, interlock power loss, broken-request, and charge-input
  bounce cases.
- Release only after P3-PWR-001 captures output levels/timing and confirms both
  #2808-M `CTRL` and DRV8833 `SLP` go low without firmware help.

## Rollback

Do not install a failed board. Preserve the W1 circuit contract, correct the
PCB as a new revision, regenerate a distinct fabrication package, and repeat
the full two-board qualification. Do not fall back to a user-operated charging
disconnect.

## Links

- `docs/decisions/0004-zero-touch-charging-and-autonomous-dock.md`
- `electronics/pcb/charging-interlock-rev-a/README.md`
- `electronics/diagrams/charging-interlock.svg`
- `electronics/prototype-netlist.csv`
- `docs/hardware/mechanical-envelope.md`
