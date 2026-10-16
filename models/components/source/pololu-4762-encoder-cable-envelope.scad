// Pololu #4762 straight stock/service envelope.
// Units: mm.
//
// Pololu specifies a 120 mm cable with six 28 AWG conductors and a 6-pin
// female JST SH-style connector. The JST SH housing envelope is modeled as
// 9 x 5 x 2.9 mm. Route a sweep from the same cross-section in the final
// assembly; this straight model is only a length and storage-volume check.

cable_length = 120.00;
connector_depth = 5.00;
connector_width = 9.00;
connector_height = 2.90;

wire_bundle_width = 6.00;
wire_bundle_height = 1.20;

union() {
    cube([connector_depth, connector_width, connector_height]);
    translate([
        connector_depth - 0.10,
        (connector_width - wire_bundle_width) / 2,
        (connector_height - wire_bundle_height) / 2
    ])
        cube([
            cable_length - connector_depth + 0.10,
            wire_bundle_width,
            wire_bundle_height
        ]);
}
