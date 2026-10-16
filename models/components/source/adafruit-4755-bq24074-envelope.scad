// Adafruit #4755 BQ24074 charger enclosure-fit mock.
// Units: mm. PCB outline and mounting holes come from Adafruit's published
// Eagle board source. Connector bodies are conservative service envelopes.

$fn = 48;
pcb_x = 38.10;
pcb_y = 33.02;
pcb_z = 1.60;

module rounded_pcb() {
    hull() {
        for (x = [2.54, pcb_x - 2.54])
            for (y = [2.54, pcb_y - 2.54])
                translate([x, y, 0]) cylinder(r = 2.54, h = pcb_z);
    }
}

difference() {
    rounded_pcb();
    for (x = [2.54, 35.56])
        for (y = [2.54, 30.48])
            translate([x, y, -0.1]) cylinder(d = 2.50, h = pcb_z + 0.2);
}

// USB-C receptacle, 2.1 mm barrel jack, battery and load JST-PH connectors.
translate([0, 5.55, pcb_z]) cube([9.0, 9.3, 4.2]);
translate([0, 17.22, pcb_z]) cube([12.1, 9.0, 8.0]);
translate([30.54, 6.80, pcb_z]) cube([7.56, 8.0, 5.0]);
translate([30.54, 18.23, pcb_z]) cube([7.56, 8.0, 5.0]);
translate([5.08, 0, pcb_z]) cube([27.94, 3.0, 8.5]);
translate([11.0, 7.0, pcb_z]) cube([19.0, 16.0, 3.2]);
