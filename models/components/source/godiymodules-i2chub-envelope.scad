// GODIYMODULES I2Chub / I2Cadapter (Amazon ASIN B0DGQBFSKL) fit-check mock.
// Units: mm. The marketplace listing supplies no mechanical drawing. This is
// a deliberately conservative envelope based on its ten 0.1 in I2C outlets
// and supplied XH2.54/straight/right-angle header options. Measure the
// delivered board and replace these dimensions before releasing a mount.

$fn = 32;
pcb_x = 55.0;
pcb_y = 30.0;
pcb_z = 1.6;

union() {
    cube([pcb_x, pcb_y, pcb_z]);
    for (x = [4.5 : 5.1 : 50.4])
        translate([x - 1.6, 3.0, pcb_z - 0.1]) cube([3.2, 24.0, 10.5]);
    translate([-3.0, 5.0, pcb_z - 0.1]) cube([3.1, 20.0, 8.1]);
}
