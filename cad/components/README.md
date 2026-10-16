# Sherman Component Model Inventory

This directory records enclosure-fit geometry for every carried component in
`docs/hardware/shopping-list.csv`. Run `./fetch-models.sh` from this directory
to populate the ignored `vendor/` cache with the exact files selected by the
inventory.

The checked-in, enclosure-ready library (including the generated fit mocks) is
in `models/components/`. This directory remains the source-discovery and fetch
record.

## Result

- 15 of 18 BOM lines have exact manufacturer 3D solids.
- Adafruit publishes both STEP and STL for its battery, charger, and fuel gauge.
- The other exact solids are STEP/STP. Keep them as B-rep solids for enclosure
  design; mesh conversion to STL throws away useful faces, holes, and datums.
- The Luckfox Pico Ultra W and SC3336 Camera B have exact manufacturer 2D
  drawings but no verified public 3D solid.
- The Pololu #4762 encoder cable is flexible and has no useful public component
  solid. Model its routed harness and connector/bend service volume in the robot
  assembly instead.

The source URLs, selected archive members, hashes, and limitations are in
`model-sources.csv`. Vendor files remain out of Git because several vendors do
not publish clear redistribution terms. The fetch script is the reproducible
record of how to obtain them.

## Known fit-model gaps

### Luckfox Pico Ultra W

Luckfox's forum attachment is a dimensioned DWG, despite the forum reply
calling it a 3D/STP file. Inspection with LibreDWG 0.13.3 found only 2D line,
arc, circle, and text entities. Its board outline is 50 x 50 mm with 2 mm corner
radii. Use that drawing for the footprint, then measure the received board's
top and bottom component heights, mounting features, USB/Ethernet access,
camera/display FFC mating paths, and Wi-Fi antenna keep-out before creating the
fit solid.

### SC3336 3MP Camera B

The manufacturer drawing defines a 25 x 24 mm board, 1.2 mm PCB, 14 mm lens
barrel diameter, 23.95 +/- 0.2 mm front-to-PCB depth, and 2 mm rear connector
projection. Build the first envelope from those values, but verify the received
lens barrel, focus travel, FFC exit, and optical axis before freezing the front
cassette.

### Pololu #4762 encoder cable

The motor STEP already includes the exact back-entry connector. In the robot
assembly, add the 120 mm cable as a routed sweep plus the minimum bend radius,
strain-relief allowance, and connector insertion/removal path. A straight STL
of a flexible cable would be actively misleading.

## Use policy

1. Fetch the source models with `./fetch-models.sh`.
2. Use STEP/STP directly in the enclosure assembly; use STL only where the CAD
   tool cannot consume STEP.
3. Compare every solid with the received part and record measured deviations.
4. Add cable bend volumes, connector mating paths, optical keep-outs, battery
   swelling allowance, and assembly motion separately; vendor component solids
   do not include those design volumes.
