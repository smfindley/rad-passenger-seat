// Optional slicer modifier: two 40 mm cylinders covering the bolt pads of the
// half. Load this in Orca as a Modifier on the object, then set its sparse
// infill density to 100%.
//
// Coordinates match out/seat_board_half.3mf, which is centred on the origin.
include <seat_board_lib.scad>

seam_depth = 16;
seam_gap   = 0.15;

// the half spans x = -board_len/2 .. seam_depth-gap, so this centres it
dx = (board_len / 2 - seam_depth + seam_gap) / 2;

for (sy = [-1, 1])
    translate([-pitch_x / 2 + dx, sy * pitch_y / 2, 0])
        cylinder(d = 40, h = total_height, $fn = 96);
