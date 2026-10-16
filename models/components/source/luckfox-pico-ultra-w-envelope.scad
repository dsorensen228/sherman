// Luckfox Pico Ultra W enclosure-fit mock.
// Units: mm.
//
// Hard dimensions come from the Luckfox board drawing and product dimension
// image. Component heights are conservative nominal envelopes based on the
// installed connector families and must be checked against the received board
// before finalizing port cutouts or standoffs.

$fn = 64;

board_x = 50.00;
board_y = 50.00;
board_r = 2.00;
pcb_thickness = 1.60;

mount_hole_d = 3.00;
mount_hole_edge = (50.00 - 45.10) / 2;

module rounded_xy_prism(size_x, size_y, radius, height) {
    linear_extrude(height = height)
        offset(r = radius)
            translate([radius, radius])
                square([size_x - 2 * radius, size_y - 2 * radius]);
}

module pcb() {
    difference() {
        rounded_xy_prism(board_x, board_y, board_r, pcb_thickness);
        for (x = [mount_hole_edge, board_x - mount_hole_edge])
            for (y = [mount_hole_edge, board_y - mount_hole_edge])
                translate([x, y, -0.1])
                    cylinder(d = mount_hole_d, h = pcb_thickness + 0.2);
    }
}

module component_block(origin, size) {
    translate(origin) cube(size);
}

union() {
    pcb();

    // Tall edge connectors. Y=0 is the Ethernet/USB-A edge.
    component_block([6.10, 0.00, pcb_thickness], [16.30, 21.00, 13.50]); // RJ45
    component_block([24.90, 0.00, pcb_thickness], [7.70, 19.00, 6.80]);  // USB-A
    component_block([20.68, 43.80, pcb_thickness], [8.64, 6.20, 3.20]); // USB-C

    // The dimension drawing fixes the header start and length.
    component_block([0.80, 6.56, pcb_thickness], [2.54, 30.48, 8.50]);
    component_block([46.66, 6.56, pcb_thickness], [2.54, 30.48, 8.50]);

    // FFC connectors and mechanically significant onboard blocks.
    component_block([6.10, 25.20, pcb_thickness], [4.20, 19.20, 3.00]); // LCD FFC
    component_block([11.70, 26.20, pcb_thickness], [4.20, 16.40, 3.00]); // Camera FFC
    component_block([32.20, 2.20, pcb_thickness], [12.30, 13.00, 2.50]); // Wi-Fi shield
    component_block([19.80, 20.00, pcb_thickness], [12.50, 13.50, 1.50]); // SoC
    component_block([32.20, 18.00, pcb_thickness], [12.20, 14.20, 1.50]); // eMMC/RAM
    component_block([22.60, 17.00, pcb_thickness], [10.20, 3.20, 4.00]); // PoE header
    component_block([34.10, 15.80, pcb_thickness], [5.00, 4.20, 3.70]);  // RTC header

    // User, boot, and reset buttons near the USB-C edge.
    for (x = [33.00, 38.00, 43.00])
        component_block([x, 45.20, pcb_thickness], [3.80, 3.20, 3.50]);

    // U.FL antenna connector and microphone package.
    component_block([40.20, 0.80, pcb_thickness], [3.30, 3.30, 1.80]);
    component_block([46.00, 4.10, pcb_thickness], [2.20, 2.20, 1.30]);
}
