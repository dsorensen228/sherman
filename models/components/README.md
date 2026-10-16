# Sherman Component Models

> Public snapshot: twelve Pololu, Waveshare, and Luckfox manufacturer downloads
> are omitted pending confirmation of redistribution terms. The descriptions and
> checks below cover the complete local library. Obtain omitted files from the
> source URLs in `manifest.csv` before running full-library validation.

This is the checked-in component-model library for enclosure and chassis work.
It covers every line in `docs/hardware/shopping-list.csv` once; spare quantities
reuse the same model.

## Contents

- `step/`: 15 exact manufacturer STEP/STP solids. Use these for normal CAD.
- `stl/`: three exact Adafruit meshes plus seven dimensioned fit-check mocks.
- `source/`: editable OpenSCAD sources for the seven generated mocks.
- `drawings/`: manufacturer drawings used where no solid was available.
- `licenses/`: licenses supplied with the Adafruit and Raspberry Pi models.
- `manifest.csv`: BOM-to-model mapping, source URL, confidence, and fit notes.
- `power-board-manifest.csv`: physical quantities for the carried charging
  subsystem; it includes one new #4755 charger and one populated interlock.
- `SHA256SUMS`: integrity record for exact models, mock sources, drawings, and licenses.

STEP is the primary format when available. It retains analytic faces, holes,
and datums that are lost in an STL mesh.

## Generated fit-check mocks

| Model | Overall bounds | Hard dimensions | Conservative/nominal details |
| --- | --- | --- | --- |
| Luckfox Pico Ultra W | `50 x 50 x 15.1 mm` | board outline, `R2` corners, `45.10 mm` vertical mounting-hole spacing, header start/length, USB-C position | connector and component heights; verify the received board before freezing port cutouts |
| SC3336 Camera B | `25 x 24 x 25.95 mm` | PCB, lens diameter, front-to-PCB depth, rear connector projection and width | mounting-hole diameter, lens-base block, connector depth |
| Pololu #4762 cable | `120 x 9 x 2.9 mm` | cable length, conductor count/gauge, connector family/pin count | straight bundled-wire and JST housing envelope; route it in the assembly |
| Adafruit #4755 BQ24074 charger | `38.10 x 33.02 x 10.10 mm` | PCB outline and four `Ø2.5 mm` mounting holes | connector bodies are conservative envelopes; add USB-C/DC/JST plug insertion paths in the assembly |
| GODIYMODULES I2Chub (B0DGQBFSKL) | `58 x 30 x 12 mm` | none; marketplace listing has no drawing | intentionally conservative board/connector envelope; measure the delivered item before designing a mount |
| Sherman charge-interlock Rev B | `38.10 x 24.13 x 11.78 mm` | original PCB outline and four `Ø2.2 mm` M2 holes; corrected Rev B pad and body locations | manufacturer maximum bodies, including socket/IC; add underside solder and harness clearance |
| Sherman charge-interlock Rev A (archive only) | `38.10 x 24.13 x 11.60 mm` | historical model retained for provenance | rejected PCB; do not use for current enclosure fit |

The mocks intentionally contain no cosmetic detail. They are collision bodies
for layout, shell clearance, connector access, and early printed fit checks.
They do not include cable bend volumes, connector insertion motion, optical
fields of view, antenna keep-outs, battery swelling, or tolerance clearance;
add those separately in the robot assembly.

## Mock coordinate conventions

- Ultra W: `X` left-to-right, `Y` from the Ethernet/USB-A edge toward USB-C,
  and `Z=0` at the PCB underside.
- Camera: `X/Y` span the PCB and `Z` runs from the rear connector toward the
  lens front.
- Encoder cable: `X` runs from the JST housing to the unterminated end.
- Charge interlock: `X/Y` follow the PCB generator coordinates and `Z=0` is
  the PCB underside.

## Rebuild and validate

OpenSCAD 2021.01 or newer is sufficient:

```sh
./models/components/build-mocks.sh
python3 ./models/components/validate.py
```

The validation checks the 20-row procurement-model mapping, the carried power
board manifest (exactly one #4755 and one populated charge interlock), STEP
framing, STL structure, generated-mock bounds, closed manifold edges, and every
recorded SHA-256 hash. OpenSCAD does not emit byte-for-byte deterministic mesh
ordering, so generated STL files are checked geometrically while their SCAD
sources are checksummed.

## Redistribution note

These files are collected for Sherman's mechanical development. Adafruit and
Raspberry Pi license texts are included. Before making this model library
public, independently confirm redistribution terms for the Luckfox,
Waveshare, and Pololu source files.
