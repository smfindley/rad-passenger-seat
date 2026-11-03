// QA: does the mirrored half interfere with the original?
use <seat_board_split.scad>

intersection() {
    half();
    rotate([0, 0, 180]) half();
}
