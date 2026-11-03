// Debug: plan slice just under the rib tops to confirm the grid is connected.
use <seat_board_lib.scad>

projection(cut = true) translate([0, 0, -9.85]) seat_board();
