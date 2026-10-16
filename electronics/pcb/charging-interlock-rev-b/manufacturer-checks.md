# Rev B manufacturer checks

Checked 2026-09-13/14. Dimensions below are acceptance inputs in `verify.py`,
not values inferred from the Rev B drawing. All components mount on the top.

| Part | Independent source and checked facts |
| --- | --- |
| TI SN74HC08N | [Datasheet SCLS081J](https://www.ti.com/lit/ds/symlink/sn74hc08.pdf), page 3: top-view pin numbering; 1/2→3 and 4/5→6; 7 GND, 14 VCC. Mechanical drawing 4040049/E (page 34 in retrieved PDF): 19.69 mm maximum length, 6.60 mm maximum body width, 2.54 mm pitch, 7.62 mm formed row spacing. With notch left, pin 1 is bottom-left. |
| TE 1-2199298-3 | [Drawing 2199298/A](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=2199298&DocType=Customer+Drawing&PartCntxt=1-2199298-3): 14 positions, 15.24 mm span, 17.78 mm body length, 10.00 mm body width, 7.62 mm rows, 5.10 mm height. Verification uses a conservative 17.98 × 10.20 mm envelope in union with the longer TI IC body. |
| onsemi 2N3904BU | [Datasheet 2N3904/D](https://www.onsemi.com/download/data-sheet/pdf/2n3904-d.pdf): E/B/C at 1/2/3. Case 135AN/O, page 7: 5.20 mm maximum width, 4.19 mm depth, rounded side projects at most 2.66 mm from lead line. Bound opposite projection by 4.19−2.13=2.06 mm. Leads must be formed from 1.27 mm to 2.54 mm pitch; allow 3.5 mm body standoff. On Rev B flat face points right, emitter hole at bottom. |
| KEMET C315C104K5R5TA | [Part specification](https://search.kemet.com/component-documentation/download/specsheet/C315C104K5R5TA): 3.81 mm max length, 2.54 mm max thickness, 3.14 mm max body height, lead pitch 2.54 ±0.78 mm. Standard 2.50 mm PCB pitch differs by 0.04 mm and lies within this range. Nonpolar. |
| Yageo MFR-25 resistors | [MFR datasheet](https://yageogroup.com/content/datasheet/asset/file/YAGEO-MFR_DATASHEET): body length 6.3 ±0.5 mm and diameter 2.4 ±0.2 mm. Checked 2.60 mm body diameter; vertical mounting at 2.54 mm lead pitch. R2's body sits on its right pad, R3's on its upper pad, other resistor bodies on their left pads. |
| Samtec TSW-140-07-L-S | [TSW straight-pin catalog, page 1](https://suddendocs.samtec.com/catalog_english/tsw_th.pdf): 2.54 mm pitch and 2.54 mm single-row insulator width; use the ordered strip cut into 5/3/3 positions. Verification reserves 2.70 mm wide insulator envelopes. Header contact numbering and drill centers are independently checked in the exported copper. |
| M2 mounting hardware | Original four Ø2.20 mm holes, at (2.54,2.54), (35.56,2.54), (2.54,21.59), (35.56,21.59) mm from top-left. Reserve Ø4.40 mm head/stand-off area plus 0.3048 mm copper clearance. No oversized washer is included in this allowance. |

Stock KiCad footprints are snapshotted under `vendor/` from the official KiCad
10.0.6 distribution. U1 pad numbering is never created by the routing script.
The J2 `_OpenSilk` variant removes two decorative outline segments so its pin
labels fit; its pads, drills and courtyard are identical to the stock footprint.
The STEP pictures are illustrative stock models. The dimensional envelope
checks above, rather than the appearance of those models, determine fit.

The independent circuit reference is `expected-circuit.json`, transcribed from
W1's pin-level schematic and manufacturer pinouts. Verification reconstructs
copper islands from the actual Gerbers and connects layers only through the
exported plated drills; it does not accept Gerber net labels as connectivity.
