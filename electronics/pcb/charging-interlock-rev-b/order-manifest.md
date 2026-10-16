# Rev B replacement order — awaiting payment

Reviewed 2026-09-14. OSH Park has received the order for **3 bare Rev B boards
for $7.10 total**, with **After Dark (black substrate, clear mask)** selected
and free USPS shipping. The order page explicitly says **awaiting payment**.
The exact population kit is reused from the 2026-09-01 parts order.

- [Order and payment page](https://oshpark.com/)
- [Verified upload](https://oshpark.com/uploads/xMWcsOYq)
- [Fabrication ZIP](charging-interlock-rev-b-gerbers.zip)

The final upload includes R2's label directly beside its resistor. The earlier
unapproved draft upload `x9QPH8bv` is superseded and must not be ordered.

| Fabrication setting | Prepared value |
| --- | --- |
| Quantity | 3 bare boards |
| Layers | 2 |
| Outline | 38.10 × 24.13 mm / 1.50 × 0.95 in |
| Mounts | Original four Ø2.20 mm M2 holes |
| Thickness / copper | 1.6 mm / 1 oz |
| Material / finish | FR-4 / ENIG |
| Mask / legend | After Dark clear mask on black substrate / white front legend |
| Extra services | After Dark selected; no paid speed upgrade |
| Order total / shipping | $7.10 total / free USPS ($0.00) |
| Assembly | None; populate two after receiving checks |

The live vendor parser reported 2 layers and 1.50 × 0.95 in (38.1 × 24.1 mm,
its rounded display). It merged the separate PTH and NPTH drill files. Its only
noncritical warning was the intentionally absent bottom silkscreen. The composite
boards, outline, drills, copper layers, masks and corrected top legend were
visually inspected in the vendor review. No missing layer, reversed top legend,
misaligned drill origin or broken outline was observed.

ZIP SHA-256:

`d9ba6e3c8fd9c93bd8e72c9271261505459c7a4d167a5aedaf82dc8cf47322cb`

[SHA256SUMS](SHA256SUMS) covers the source PCB, ZIP and eight fabrication files.
Each archive entry was compared byte-for-byte with the independently verified
fabrication input. The final PCB matches [validation.json](validation.json).

The order payment page is open in the task's browser. Its current state is
received and unpaid, with fabrication scheduled only after payment. The final
After Dark selection changes the mask/substrate appearance, not the PCB geometry.
No address or payment information is stored in this repository.

Use the [assembly and receiving procedure](README.md) once Rev B arrives.
P3-PWR-001 still requires two-board measured truth-table and fault qualification;
this prepared order is not permission for mobile operation.

Service reference: [OSH Park After Dark specifications](https://docs.oshpark.com/services/afterdark/),
checked 2026-09-14: 1.6 mm nominal FR-4, 1 oz copper, two layers, ENIG.
