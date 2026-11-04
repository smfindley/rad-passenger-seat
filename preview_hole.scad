// Axial section through the bolt station at x = +112.
use <seat_board_lib.scad>

intersection() {
    difference() {
        seat_board();
        translate([112, -400, -50]) cube([800, 800, 200]);
    }
    translate([45, 28, -5]) cube([200, 54, 40]);
}
