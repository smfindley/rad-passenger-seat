// =====================================================================
//  RAD passenger seat - two-piece board for a 220 x 220 bed
//
//  Split at the board's centre line, x = 0. The seam is a dovetail comb:
//  four trapezoidal teeth with a 10 deg undercut, so the halves key
//  together mechanically and cannot pull apart in X. The pattern is odd
//  about y = 0, which makes the two halves IDENTICAL: print this file
//  twice and turn one part 180 deg about Z to mate it.
//
//  Assembly is a straight vertical drop - the seam is a constant-Z
//  profile, so both halves print flat with no supports and the joint
//  faces come off the printer square.
//
//  All dimensions in millimetres.
// =====================================================================

include <seat_board_lib.scad>

/* [Interlock] */
seam_depth    = 16.0;    // tooth reach either side of x = 0
seam_angle    = 10;      // dovetail undercut, degrees
seam_teeth    = 4;       // even number, so halves are identical
seam_root_w   = 18.0;    // tooth width where it meets the seam line
seam_fillet   = 1.0;     // rounds the tooth roots (stress relief)
seam_gap      = 0.15;    // clearance per side -> 0.30 mm glue line

// Move the inner cross ribs off the seam so the joint runs through a
// clean flat band instead of splitting a rib down its centre.
split_cross_ribs = [-pitch_x / 2, -25, 25, pitch_x / 2];

// ---------------------------------------------------------------------
seam_pitch = board_wid / seam_teeth;
root_half  = seam_root_w / 2;
tip_half   = root_half + seam_depth * tan(seam_angle);
seam_top   = thickness + (reinforce ? boss_h : 0);

centres = [for (i = [0 : seam_teeth - 1])
              (i - (seam_teeth - 1) / 2) * seam_pitch];
dirs    = [for (i = [0 : seam_teeth - 1]) (i % 2 == 0) ? 1 : -1];

function tooth_pts(yc, d) = [
    [0,       yc - root_half],
    [d * seam_depth, yc - tip_half],
    [d * seam_depth, yc + tip_half],
    [0,       yc + root_half]
];

seam_points = concat(
    [[-400, -200], [0, -200]],
    [for (i = [0 : seam_teeth - 1]) each tooth_pts(centres[i], dirs[i])],
    [[0, 200], [-400, 200]]
);

module seam_profile() {
    polygon(points = seam_points);
}

// closing rounds the concave tooth roots; the delta offset leaves the
// glue clearance on every joint face.
module piece_profile() {
    offset(delta = -seam_gap)
        offset(r = -seam_fillet)
            offset(r = seam_fillet)
                seam_profile();
}

// ---------------------------------------------------------------------
module half() {
    intersection() {
        seat_board(cross_ribs = split_cross_ribs);
        linear_extrude(seam_top + 4) piece_profile();
    }
}

show = "half";   // [half, pair, exploded, seam]

if (show == "half") {
    half();
} else if (show == "seam") {
    piece_profile();
} else if (show == "pair") {
    half();
    rotate([0, 0, 180]) half();
} else {
    color("SteelBlue") half();
    color("Goldenrod") translate([45, 0, 0]) rotate([0, 0, 180]) half();
}
