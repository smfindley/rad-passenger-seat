// =====================================================================
//  RAD passenger seat - shared board geometry (no top-level object)
//  Included by seat_board.scad (one piece) and seat_board_split.scad
//  (two interlocking halves).
//  All dimensions in millimetres.
// =====================================================================

/* [Seat footprint] */
seat_len      = 11.5 * 25.4;   // 292.1  cushion overall length
seat_wid      = 6.0  * 25.4;   // 152.4  cushion overall width
side_clear    = 2.5;           // margin per side inside the cover (5 mm total)
corner_r      = 18;            // plan-view corner radius
edge_chamfer  = 0.8;           // chamfer on top and bottom perimeters

/* [Bolt pattern - centred] */
pitch_x       = 224;           // eye-to-eye, along length
pitch_y       = 110;           // eye-to-eye, across width
bolt_hole_d   = 6.8;           // M6 clearance
hex_af        = 10.0;          // M6 hex head across flats
hex_fit       = 0.6;           // total clearance in hex trap (print tolerance)
hex_depth     = 5.5;           // trap depth from the top of the boss
hex_lead      = 0.8;           // lead-in chamfer at trap mouth
hex_rot       = 0;             // 0 deg = flats parallel to X axis

/* [Height budget] */
// total_height is the only dimension the cover cares about. Everything
// above the plate (ribs, rim, bolt pads) is packed into the leftover.
total_height  = 10.0;
thickness     = 7.5;           // plate; the remainder becomes rib depth

/* [Reinforcement] */
reinforce     = true;          // bosses + rib grid on the cushion face
boss_d        = 26;            // pad diameter at each bolt
boss_fillet   = 2.5;           // 45 deg blend into the plate
rib_w         = 6.0;           // rib width at the base
rib_top_w     = 3.5;           // rib width at the top
rim           = true;          // closed perimeter rib = torsion box
rim_inset     = 8.0;           // board edge to rim outer face
rim_w         = 6.0;           // rim width
rib_inset     = 6.0;           // rib end clearance when the rim is off

rib_h         = total_height - thickness;
boss_h        = rib_h;
rib_reach     = rim ? rim_inset + rim_w / 2 : rib_inset;

// ---------------------------------------------------------------------
board_len = seat_len - 2 * side_clear;
board_wid = seat_wid - 2 * side_clear;
hex_d     = (hex_af + hex_fit) / cos(30);   // across-corners of trap
hex_top   = thickness + (reinforce ? boss_h : 0);

$fn = 64;

// ---------------------------------------------------------------------
module rrect(l, w, r) {
    offset(r = r, $fn = 128) square([l - 2 * r, w - 2 * r], center = true);
}

// plate with chamfered top and bottom perimeter
module slab(l, w, r, h, c) {
    hull() {
        linear_extrude(0.01)          offset(delta = -c) rrect(l, w, r);
        translate([0, 0, c])          linear_extrude(0.01) rrect(l, w, r);
        translate([0, 0, h - c])      linear_extrude(0.01) rrect(l, w, r);
        translate([0, 0, h - 0.01])   linear_extrude(0.01) offset(delta = -c) rrect(l, w, r);
    }
}

// conical-skirted pad around a bolt station
module boss() {
    // keep the fillet control below the boss top so the hull cannot overshoot
    // the height envelope when boss_h equals boss_fillet
    fillet = min(boss_fillet, boss_h - 0.1);
    hull() {
        translate([0, 0, thickness - 0.01])
            cylinder(d = boss_d + 2 * fillet, h = 0.02, $fn = 96);
        translate([0, 0, thickness + fillet])
            cylinder(d = boss_d, h = 0.01, $fn = 96);
        translate([0, 0, hex_top - 0.01])
            cylinder(d = boss_d, h = 0.01, $fn = 96);
    }
}

// one tapered rib, length along local X, centred on local origin.
// ztop is nudged per rib family so no two top faces end up coplanar.
module rib(len, ztop) {
    hull() {
        translate([0, 0, thickness - 0.01])
            cube([len, rib_w, 0.02], center = true);
        translate([0, 0, ztop - 0.01])
            cube([len, rib_top_w, 0.02], center = true);
    }
}

// closed loop around the perimeter - ties every rib into a torsion box
module rim_ring() {
    z0 = thickness - 0.01;
    z1 = hex_top - 0.09;
    translate([0, 0, z0])
        difference() {
            linear_extrude(z1 - z0)
                rrect(board_len - 2 * rim_inset, board_wid - 2 * rim_inset,
                      max(0.5, corner_r - rim_inset));
            translate([0, 0, -1])
                linear_extrude(z1 - z0 + 2)
                    rrect(board_len - 2 * rim_inset - 2 * rim_w,
                          board_wid - 2 * rim_inset - 2 * rim_w,
                          max(0.5, corner_r - rim_inset - rim_w));
        }
}

module bolt_station() {
    translate([0, 0, -1])
        cylinder(d = bolt_hole_d, h = hex_top + 3, $fn = 64);

    translate([0, 0, hex_top - hex_depth])
        cylinder(d = hex_d, h = hex_depth + 1, $fn = 6);

    translate([0, 0, hex_top - hex_lead])
        hull() {
            cylinder(d = hex_d, h = 0.01, $fn = 6);
            translate([0, 0, hex_lead])
                cylinder(d = hex_d + 2 * hex_lead, h = 0.01, $fn = 6);
        }
}

// cross_ribs is exposed so the split version can move the centre ribs
// clear of the interlocking seam.
module seat_board(cross_ribs = [-pitch_x / 2, 0, pitch_x / 2]) {
    difference() {
        union() {
            slab(board_len, board_wid, corner_r, thickness, edge_chamfer);

            if (reinforce) {
                for (sx = [-1, 1], sy = [-1, 1])
                    translate([sx * pitch_x / 2, sy * pitch_y / 2, 0])
                        boss();

                if (rim)
                    rim_ring();

                for (y = [-pitch_y / 2, 0, pitch_y / 2])
                    translate([0, y, 0])
                        rib(board_len - 2 * rib_reach, hex_top - 0.05);

                for (x = cross_ribs)
                    translate([x, 0, 0])
                        rotate([0, 0, 90])
                            rib(board_wid - 2 * rib_reach, hex_top - 0.12);
            }
        }

        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * pitch_x / 2, sy * pitch_y / 2, 0])
                rotate([0, 0, hex_rot])
                    bolt_station();
    }
}
