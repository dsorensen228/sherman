# ADR 0007: Replace Rev A with same-size Rev B and independent fabrication checks

## Status

Accepted for replacement design and order preparation, 2026-09-14, following the
owner's instructions to prepare Rev B, strengthen validation, and keep it compact.
This supersedes the Rev A fabrication selection and verification method in
ADR 0005. Physical acceptance and mobile release remain BLOCKED-HARDWARE under
P3-PWR-001; design verification does not certify a populated board.

## Context

Receiving review found the generated Rev A DIP-14 pin numbering mirrored relative
to the manufacturer's top view. The socket also obstructed Q1's emitter hole.
The small adjacent hole is a routing via; hiding a via is not itself an assembly
failure. Rev A's generator and structural tests shared assumptions and passed a
physically wrong footprint. Parsing a layer stack without reconstructing its
circuit was insufficient evidence. A larger replacement layout was rejected by
the owner, so original XY dimensions and mounting holes remain fixed.

## Decision

Use `electronics/pcb/charging-interlock-rev-b/`, a 38.10 × 24.13 mm, two-layer,
through-hole board with the same four Ø2.20 mm mounting holes and the same ordered
parts and W1 electrical contract. Pin 1 is lower-left with U1's notch left. Q1
moves outside the socket with its flat face right. The resistor bodies and header
locations are rearranged within the original board outline.

Use official KiCad footprint numbering and transforms plus native fabrication
export. Keep independent acceptance inputs for the W1 circuit, manufacturer's
pin diagrams and maximum component-body dimensions. KiCad DRC and an independent
Gerbonara/Shapely analysis of copper, drills, mask, edge and mounting-head
clearances must pass before packaging. Regression tests must reject Rev A and
injected orientation, obstruction, short and open faults. Review the actual
manufacturer upload preview and retain the ZIP checksum with its order record.

## Alternatives

- Salvage Rev A with bottom-side IC placement or wiring: rejected; replace this
  small safety-relevant board and preserve an uncomplicated assembly procedure.
- Enlarge the board: rejected by the owner; the corrected layout fits the original.
- Switch to SMD: unnecessary and would discard the already ordered population kit.
- Trust the generator's own checks: rejected by the observed common-mode failure.

## Consequences

Rev A boards are quarantined and preserved in source as negative controls.
Three replacement bare boards can be prepared using the existing population kit
for two assemblies. The original XY mounting envelope remains unchanged. The
updated mechanical model uses manufacturer maximum socket/IC heights, raising the
conservative Z bound from the old 11.60 mm model to 11.78 mm; this is an envelope
correction for the same parts, not a new board or mounting requirement. Downstream
enclosure work must use Rev B and still reserve solder and harness clearance.

## Verification

P3-PWR-003 records zero KiCad DRC violations and unconnected items, independent
copper connectivity for all 44 pads, manufacturer body and hole-access checks,
and eight regression tests including deliberate corruption. The minimum measured
layout body gap is 0.702 mm and different-net copper clearance is 0.508 mm.
Vendor review and quote are recorded in the Rev B order manifest. Receiving,
continuity and both-board truth-table/fault testing remain required in P3-PWR-001.

## Rollback

If Rev B fails any fabrication or receiving check, quarantine it and revise the
board. Keep motor operation inhibited. Do not re-authorize Rev A or introduce a
manual charging disconnect.

## Links

- [Rev B assembly and validation](../../electronics/pcb/charging-interlock-rev-b/README.md)
- [Primary manufacturer checks](../../electronics/pcb/charging-interlock-rev-b/manufacturer-checks.md)
- [Work packet](../../artifacts/phase-3/P3-PWR-003/PACKET.md)
- [ADR 0005](0005-dedicated-charge-interlock-pcb.md)
