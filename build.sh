#!/bin/sh
# Rebuild every STL and preview render.
set -e
cd "$(dirname "$0")"
mkdir -p out

# ---- one piece -------------------------------------------------------
openscad -o out/seat_board.stl --export-format binstl seat_board.scad

openscad -o out/preview_iso.png --imgsize=1600,1200 \
  --camera=0,0,6,58,0,28,0 --viewall --projection=p \
  --colorscheme=Tomorrow --render=true seat_board.scad

openscad -o out/preview_top.png --imgsize=1600,900 \
  --camera=0,0,0,0,0,0,0 --viewall --projection=o \
  --colorscheme=Tomorrow --render=true seat_board.scad

openscad -o out/preview_bottom.png --imgsize=1600,900 \
  --camera=0,0,6,180,0,0,330 --projection=o \
  --colorscheme=Tomorrow --render=true seat_board.scad

openscad -o out/preview_hole.png --imgsize=1600,900 \
  --camera=240,150,120,80,55,5 --projection=p \
  --colorscheme=Tomorrow --render=true preview_hole.scad

openscad -o out/slice_check.png --imgsize=1600,900 \
  --camera=0,0,0,0,0,0,0 --viewall --projection=o \
  --colorscheme=Tomorrow slice_check.scad

# ---- two piece -------------------------------------------------------
openscad -o out/seat_board_half.stl --export-format binstl seat_board_split.scad

openscad -o out/bolt_pad_modifier.stl --export-format binstl bolt_pad_modifier.scad

./make_3mf.py out/seat_board_half.stl out/seat_board_half.3mf \
  --title "RAD passenger seat base board - half" \
  --desc "161.4 x 151.4 x 10.0 mm. Print twice, rotate one part 180 deg about Z to mate the dovetail seam. 6 walls, 50% gyroid, PLA."

openscad -o out/preview_half_iso.png --imgsize=1600,1200 \
  --camera=0,0,6,58,0,28,0 --viewall --projection=p \
  --colorscheme=Tomorrow --render=true seat_board_split.scad

openscad -o out/preview_split_top.png --imgsize=1600,900 -D 'show="pair"' \
  --camera=0,0,0,0,0,0,0 --viewall --projection=o \
  --colorscheme=Tomorrow --render=true seat_board_split.scad

openscad -o out/preview_split_pair_iso.png --imgsize=1600,1200 -D 'show="pair"' \
  --camera=0,0,6,58,0,28,0 --viewall --projection=p \
  --colorscheme=Tomorrow --render=true seat_board_split.scad

openscad -o out/preview_split_exploded.png --imgsize=1600,1200 -D 'show="exploded"' \
  --camera=0,0,8,58,0,20,0 --viewall --projection=p \
  --colorscheme=Tomorrow --render=true seat_board_split.scad

openscad -o out/seam_profile.png --imgsize=1400,1200 -D 'show="seam"' \
  --camera=0,0,0,0,0,0,180 --projection=o \
  --colorscheme=Tomorrow seat_board_split.scad

# ---- strip the eXIf chunk OpenSCAD stamps into every PNG -------------
# (legal PNG, but rejected as "corrupt" by some viewers and validators)
./clean_png.py 'out/*.png'

# ---- checks ----------------------------------------------------------
python3 check_stl.py out/seat_board.stl
python3 check_stl.py out/seat_board_half.stl

openscad -o out/_gap_check.stl --export-format binstl check_pair.scad >/dev/null 2>&1 || true
[ -s out/_gap_check.stl ] && python3 check_stl.py out/_gap_check.stl || true
rm -f out/_gap_check.stl
