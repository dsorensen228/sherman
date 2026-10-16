// Luckfox/Waveshare SC3336 3MP Camera B enclosure-fit mock.
// Units: mm.
//
// Manufacturer drawing dimensions:
// - PCB: 25 x 24 x 1.2
// - lens barrel: 14 diameter
// - lens-front to rear PCB face: 23.95 +/- 0.2
// - rear FFC connector projection: 2
// - connector width: 14.2

$fn = 96;

board_x = 25.00;
board_y = 24.00;
board_r = 2.00;
pcb_thickness = 1.20;

rear_connector_projection = 2.00;
front_to_rear_pcb = 23.95;
overall_depth = rear_connector_projection + front_to_rear_pcb;

lens_d = 14.00;
lens_center = [board_x / 2, board_y / 2];

mount_hole_d = 2.00;
corner_hole_x = [2.00, 23.00];
corner_hole_y = [5.25, 18.75];
side_hole_x = [3.50, 21.50];
side_hole_y = board_y / 2;

module rounded_xy_prism(size_x, size_y, radius, height) {
    linear_extrude(height = height)
        offset(r = radius)
            translate([radius, radius])
                square([size_x - 2 * radius, size_y - 2 * radius]);
}

module pcb() {
    translate([0, 0, rear_connector_projection])
        difference() {
            rounded_xy_prism(board_x, board_y, board_r, pcb_thickness);
            for (x = corner_hole_x)
                for (y = corner_hole_y)
                    translate([x, y, -0.1])
                        cylinder(d = mount_hole_d, h = pcb_thickness + 0.2);
            for (x = side_hole_x)
                translate([x, side_hole_y, -0.1])
                    cylinder(d = mount_hole_d, h = pcb_thickness + 0.2);
        }
}

union() {
    pcb();

    // Rear FFC connector, centered along the lower board edge.
    translate([(board_x - 14.20) / 2, 0.50, 0])
        cube([14.20, 4.20, rear_connector_projection]);

    // Blocky lens base and the maximum-diameter barrel envelope.
    translate([4.50, 4.00, rear_connector_projection + pcb_thickness])
        cube([16.00, 16.00, 2.50]);
    translate([lens_center[0], lens_center[1], rear_connector_projection + pcb_thickness + 2.50])
        cylinder(
            d = lens_d,
            h = overall_depth - (rear_connector_projection + pcb_thickness + 2.50)
        );
}
