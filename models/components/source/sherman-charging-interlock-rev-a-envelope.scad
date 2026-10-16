// Populated Sherman charge-interlock Rev A enclosure-fit model.
// Units: mm. Board size, mounting holes, pad centers, and component placement
// come from electronics/pcb/charging-interlock-rev-a/generate.py. Component
// bodies are conservative envelopes for the exact ordered through-hole parts.

$fn = 40;

pcb_x = 38.10;
pcb_y = 24.13;
pcb_z = 1.60;
mount_hole_d = 2.20;

module pcb() {
    difference() {
        cube([pcb_x, pcb_y, pcb_z]);
        for (x = [2.54, 35.56])
            for (y = [2.54, 21.59])
                translate([x, y, -0.1])
                    cylinder(d = mount_hole_d, h = pcb_z + 0.2);
    }
}

module header(count, x, y, along_x = true) {
    pitch = 2.54;
    base_x = along_x ? count * pitch : 2.54;
    base_y = along_x ? 2.54 : count * pitch;

    translate([x - 1.27, y - 1.27, pcb_z])
        cube([base_x, base_y, 2.50]);
    for (index = [0 : count - 1]) {
        pin_x = x + (along_x ? index * pitch : 0);
        pin_y = y + (along_x ? 0 : index * pitch);
        translate([pin_x, pin_y, pcb_z - 0.1])
            cylinder(d = 0.64, h = 8.60);
    }
}

module vertical_resistor(body_x, body_y, return_x, return_y) {
    // A 1/4 W axial body mounted vertically with its return lead folded down.
    for (position = [[body_x, body_y], [return_x, return_y]])
        translate([position[0], position[1], pcb_z - 0.1])
            cylinder(d = 0.60, h = 8.20);
    translate([body_x, body_y, pcb_z + 1.20])
        cylinder(d = 2.50, h = 6.60);
}

union() {
    pcb();

    // J1 Pico, J2 charger, and J3 output harness headers.
    header(5, 6.35, 20.828);
    header(3, 26.67, 20.828);
    header(3, 13.97, 2.794);

    // U1 socket plus installed SN74HC08N PDIP-14. The combined 10 mm height
    // above the PCB is intentionally conservative for enclosure clearance.
    translate([8.89, 6.985, pcb_z])
        cube([17.78, 9.906, 3.20]);
    translate([9.65, 8.485, pcb_z + 3.20])
        cube([16.26, 6.906, 6.80]);

    // Q1, onsemi 2N3904BU TO-92, including conservative lead stand-off.
    for (x = [25.40, 27.94, 30.48])
        translate([x, 13.208, pcb_z - 0.1])
            cylinder(d = 0.60, h = 4.20);
    translate([27.94, 13.208, pcb_z + 3.50])
        cylinder(d = 5.20, h = 5.20);

    // C1, 5 mm disc capacitor envelope and its two leads.
    for (y = [13.97, 16.51])
        translate([8.382, y, pcb_z - 0.1])
            cylinder(d = 0.60, h = 6.20);
    translate([5.882, 14.74, pcb_z + 1.20])
        cube([5.00, 1.00, 6.20]);

    vertical_resistor(3.81, 18.288, 6.35, 18.288);  // R1
    vertical_resistor(25.40, 17.78, 27.94, 17.78);  // R2
    vertical_resistor(30.48, 17.78, 33.02, 17.78);  // R3
    vertical_resistor(6.35, 13.97, 3.81, 13.97);    // R4
    vertical_resistor(6.35, 10.16, 3.81, 10.16);    // R5
    vertical_resistor(6.35, 6.35, 3.81, 6.35);      // R6
    vertical_resistor(27.94, 5.588, 30.48, 5.588);  // R7
}
