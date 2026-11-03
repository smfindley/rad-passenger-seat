// Axial section through the bolt stations at x = +111.5 (both hex traps).
use <seat_board_lib.scad>

intersection() {
    difference() {
        seat_board();
        translate([111.5, -400, -50]) cube([800, 800, 200]);
    }
    translate([45, 28, -5]) cube([200, 54, 40]);
}
