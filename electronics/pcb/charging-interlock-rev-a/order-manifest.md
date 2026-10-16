# Order Manifest — Charge-Interlock Rev A

Orders placed: 2026-09-01. Order numbers, delivery address, payment data, and
final tax are intentionally not stored here. Reconcile this manifest against
the vendor shipping confirmations before marking anything received.

## Bare PCBs — OSH Park

Submitted design: <https://oshpark.com/uploads/N2Fdsrw6>

OSH Park was selected for this small prototype because its two-layer service is
US-manufactured, 1.6 mm FR-4 with 1 oz copper, ENIG finish, and free shipping.
Its published minimums are 0.1524 mm trace/space and 0.254 mm drill; this board
uses 0.4064/0.3048 mm signal-width/clearance and a 0.6096 mm minimum drill.

The vendor parser reported before submission:

- 2 layers;
- 1.50 × 0.95 inches / 38.1 × 24.1 mm;
- separate PTH and NPTH drill files found and merged correctly;
- top and bottom previews generated;
- no bottom silkscreen, intentionally—front legend only;
- 3 boards for $7.10 on the standard Prototype service.

The order was placed for three bare boards. The last recorded standard Prototype
quote was $7.10; the owner may have selected Super Swift at checkout, so the
shipping confirmation—not that quote—controls the actual service and paid total.
Both services use the same 1.6 mm, 1 oz, two-layer process needed here.

## Population parts — Mouser

The submitted Mouser order contains these interlock lines:

| Mouser # | Manufacturer part | Qty | Purpose |
| --- | --- | ---: | --- |
| `595-SN74HC08N` | TI `SN74HC08N` | 2 | U1, one per board |
| `512-2N3904BU` | onsemi `2N3904BU` | 5 | Q1 ×2 plus handling/fault-injection spares |
| `571-1-2199298-3` | TE `1-2199298-3` | 2 | U1 socket, one per board |
| `80-C315C104K5R5TA` | KEMET `C315C104K5R5TA` | 10 | C1 ×2 plus general bypass spares |
| `603-MFR-25FRF52-4K7` | Yageo `MFR-25FRF52-4K7` | 10 | R7 ×2 plus spares |
| `603-MFR-25FRF5210K` | Yageo `MFR-25FRF52-10K` | 10 | R1/R4/R5/R6 ×2 plus two spares |
| `603-MFR-25FRF52-47K` | Yageo `MFR-25FRF52-47K` | 10 | R2 ×2 plus spares |
| `603-MFR-25FBF52-100K` | Yageo `MFR-25FBF52-100K` | 10 | R3 ×2 plus spares |
| `200-TSW14007LS` | Samtec `TSW-140-07-L-S` | 1 × 40 positions | J1/J2/J3 total 22 positions; 18 spare |

Every line reported `Ships Now` immediately before submission. The
interlock-only merchandise total in that cart was $11.04 before estimated tariff
and shipping.

The submitted cart also contained `485-4755` Adafruit chargers, quantity 2,
totaling $29.90. Immediately before submission the complete cart reported
merchandise $40.94, estimated tariff $1.13, UPS Ground $8.49, and subtotal
$50.56 before tax. The final confirmation controls if any amount changed.

## Receiving reconciliation

1. Match the OSH Park shipping confirmation to three boards, the submitted ZIP,
   the selected service, and the paid total.
2. Match every Mouser manufacturer part number and quantity above, plus the two
   #4755 boards, to the packing slip. Quarantine substitutions or damaged parts.
3. Complete the bare-board inspection and unpowered continuity checks in
   [`README.md`](README.md) before populating anything.
4. Populate and qualify two boards, label them `SHERMAN` and `SPARE`, and retain
   the third PCB bare.

References: [OSH Park two-layer services](https://docs.oshpark.com/services/),
[OSH Park two-layer specifications](https://docs.oshpark.com/services/two-layer/),
and [`charging-interlock-rev-a-gerbers.zip`](charging-interlock-rev-a-gerbers.zip).
