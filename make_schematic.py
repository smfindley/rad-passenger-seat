#!/usr/bin/env python3
"""Generate dimensioned SVG schematics of the seat board.

Reads the parameters straight out of the OpenSCAD sources so the drawings
can never drift from the model, and writes:

    out/schematic_plan.svg      plan view with overall/bolt dimensions
    out/schematic_section.svg   bolt-station and plate/rib sections

Standard library only - no dependency on an SVG renderer.
"""
import ast
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

INK = "#17323c"
DIM = "#5c6f75"
FILL = "#c9e4e8"
SEAM = "#8a2f3f"
FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"


# ---------------------------------------------------------------- parameters
def _eval(node, vals):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Name) and node.id in vals:
        return vals[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand, vals)
    if isinstance(node, ast.BinOp):
        a, b = _eval(node.left, vals), _eval(node.right, vals)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            return a / b
    raise ValueError("unsupported expression")


def read_constants(path):
    vals = {}
    for raw in Path(path).read_text().splitlines():
        line = raw.split("//", 1)[0]
        m = re.match(r"\s*([A-Za-z_]\w*)\s*=\s*(.+?)\s*;\s*$", line)
        if not m:
            continue
        try:
            vals[m.group(1)] = _eval(ast.parse(m.group(2), mode="eval").body, vals)
        except Exception:
            pass
    return vals


lib = read_constants(HERE / "seat_board_lib.scad")
split = read_constants(HERE / "seat_board_split.scad")

seat_len = lib["seat_len"]
seat_wid = lib["seat_wid"]
side_clear = lib["side_clear"]
corner_r = lib["corner_r"]
pitch_x = lib["pitch_x"]
pitch_y = lib["pitch_y"]
hole_d = lib["bolt_hole_d"]
hex_af = lib["hex_af"] + lib["hex_fit"]
hex_depth = lib["hex_depth"]
H = lib["total_height"]
t = lib["thickness"]
boss_d = lib["boss_d"]
rib_w = lib["rib_w"]
rib_top_w = lib["rib_top_w"]
seam_depth = split.get("seam_depth", 16.0)

board_len = seat_len - 2 * side_clear
board_wid = seat_wid - 2 * side_clear
rib_h = H - t
fillet = min(lib["boss_fillet"], rib_h - 0.1)
pad_base_r = boss_d / 2 + fillet
hex_r = hex_af / 2 / math.cos(math.radians(30))


# ---------------------------------------------------------------------- svg
def text(x, y, s, size=15, anchor="start", fill=INK, weight="normal", rot=None):
    tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot is not None else ""
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size}" '
        f'text-anchor="{anchor}" fill="{fill}" font-weight="{weight}"{tr}>{s}</text>'
    )


def dim_h(x1, x2, y, label, size=13, dy=-9):
    return (
        f'<line x1="{x1:.2f}" y1="{y:.2f}" x2="{x2:.2f}" y2="{y:.2f}" '
        f'stroke="{DIM}" stroke-width="1.1" marker-start="url(#arrow)" '
        f'marker-end="url(#arrow)"/>'
        + text((x1 + x2) / 2, y + dy, label, size=size, anchor="middle", fill=DIM)
    )


def dim_v(x, y1, y2, label, size=13, dx=-8):
    return (
        f'<line x1="{x:.2f}" y1="{y1:.2f}" x2="{x:.2f}" y2="{y2:.2f}" '
        f'stroke="{DIM}" stroke-width="1.1" marker-start="url(#arrow)" '
        f'marker-end="url(#arrow)"/>'
        + text(x + dx, (y1 + y2) / 2, label, size=size, anchor="middle",
               fill=DIM, rot=-90)
    )


def lead(x1, y1, x2, y2):
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{DIM}" stroke-width="1"/><circle cx="{x1:.2f}" cy="{y1:.2f}" '
            f'r="2.6" fill="{DIM}"/>')


def head(w, h, title, sub):
    return (
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>'
        + text(40, 52, title, size=25, weight="bold")
        + text(40, 76, sub, size=14, fill=DIM)
    )


DEFS = (
    '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
    'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{DIM}"/></marker></defs>'
)


# ------------------------------------------------------------- plan drawing
def plan_svg():
    W, Hc = 1260, 790
    S = 3.4
    X0, Y0 = 150.0, 100.0
    bw, bh = board_len * S, board_wid * S
    xr, yb = X0 + bw, Y0 + bh

    def px(x):
        return X0 + (x + board_len / 2) * S

    def py(y):
        return Y0 + (board_wid / 2 - y) * S

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hc}" '
         f'viewBox="0 0 {W} {Hc}">', DEFS]
    s.append(head(W, Hc, "PLAN VIEW",
                  f"board {board_len:.1f} \u00d7 {board_wid:.1f} \u00d7 {H:.1f} mm "
                  f"\u00b7 {2 * side_clear:.0f} mm total clearance in the cover"))

    s.append(f'<rect x="{X0}" y="{Y0}" width="{bw:.2f}" height="{bh:.2f}" '
             f'rx="{corner_r * S:.2f}" fill="{FILL}" stroke="{INK}" '
             f'stroke-width="2.2"/>')

    # centre line + seam
    cx, cy = px(0), py(0)
    s.append(f'<line x1="{cx:.2f}" y1="{Y0}" x2="{cx:.2f}" y2="{yb:.2f}" '
             f'stroke="{SEAM}" stroke-width="2" stroke-dasharray="9 6"/>')
    s.append(text(cx + 10, Y0 + 20, "split at x = 0 (two-piece)",
                  size=12, fill=SEAM))

    # bolt stations
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx, by = px(sx * pitch_x / 2), py(sy * pitch_y / 2)
            s.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{boss_d / 2 * S:.2f}" '
                     f'fill="none" stroke="{DIM}" stroke-width="1" '
                     f'stroke-dasharray="5 4"/>')
            pts = " ".join(
                f"{bx + hex_r * S * math.cos(math.radians(30 + 60 * k)):.2f},"
                f"{by + hex_r * S * math.sin(math.radians(30 + 60 * k)):.2f}"
                for k in range(6))
            s.append(f'<polygon points="{pts}" fill="#ffffff" stroke="{INK}" '
                     f'stroke-width="1.2"/>')
            s.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{hole_d / 2 * S:.2f}" '
                     f'fill="{INK}"/>')

    # overall dimensions
    s.append(f'<line x1="{X0}" y1="{yb}" x2="{X0}" y2="{yb + 34}" stroke="{DIM}" '
             f'stroke-width=".8"/>')
    s.append(f'<line x1="{xr:.2f}" y1="{yb}" x2="{xr:.2f}" y2="{yb + 34}" '
             f'stroke="{DIM}" stroke-width=".8"/>')
    s.append(dim_h(X0, xr, yb + 46, f"{board_len:.1f}"))

    s.append(f'<line x1="{xr:.2f}" y1="{Y0}" x2="{xr + 34}" y2="{Y0}" '
             f'stroke="{DIM}" stroke-width=".8"/>')
    s.append(f'<line x1="{xr:.2f}" y1="{yb:.2f}" x2="{xr + 34}" y2="{yb:.2f}" '
             f'stroke="{DIM}" stroke-width=".8"/>')
    s.append(dim_v(xr + 46, Y0, yb, f"{board_wid:.1f}", dx=-12))

    # bolt pattern
    left, right = px(-pitch_x / 2), px(pitch_x / 2)
    top, bot = py(pitch_y / 2), py(-pitch_y / 2)
    for bx in (left, right):
        s.append(f'<line x1="{bx:.2f}" y1="{top - 10}" x2="{bx:.2f}" y2="{Y0 + 42}" '
                 f'stroke="{DIM}" stroke-width=".7" stroke-dasharray="2 3"/>')
    s.append(dim_h(left, right, Y0 + 48, "", dy=-7))
    s.append(text(left + 0.63 * (right - left), Y0 + 41, f"{pitch_x:.0f}",
                  size=13, anchor="middle", fill=DIM))
    for by in (top, bot):
        s.append(f'<line x1="{X0}" y1="{by:.2f}" x2="{X0 - 45}" y2="{by:.2f}" '
                 f'stroke="{DIM}" stroke-width=".7" stroke-dasharray="2 3"/>')
    s.append(dim_v(X0 - 45, top, bot, f"{pitch_y:.0f}", dx=-10))

    # pad + corner callouts
    s.append(lead(px(-pitch_x / 2) - boss_d / 2 * S * .7,
                  py(pitch_y / 2) - boss_d / 2 * S * .7, X0 + 26, Y0 + 150))
    s.append(text(X0 + 26, Y0 + 168, f"\u00d8{boss_d:.0f} pad", size=14, fill=DIM))

    ccx, ccy = xr - corner_r * S, Y0 + corner_r * S
    s.append(lead(ccx + corner_r * S * .707, ccy - corner_r * S * .707,
                  xr - 60, Y0 - 24))
    s.append(text(xr - 60, Y0 - 30, f"R{corner_r:.0f}", size=14, anchor="middle",
                  fill=DIM))

    s.append(text(X0, Hc - 46, f"bolt holes \u00d8{hole_d:.1f} through \u00b7 "
                  f"hex traps {hex_af:.1f} across flats \u00b7 "
                  f"{lib['hex_depth']:.1f} deep", size=13, fill=DIM))
    s.append(text(X0, Hc - 26, "dashed circle = \u00d8"
                  f"{boss_d:.0f} bolt pad \u00b7 all dimensions mm", size=13, fill=DIM))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------- section drawing
def section_svg():
    W, Hc = 1280, 740
    S = 12.0
    base = 500.0

    def zy(z):
        return base - z * S

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hc}" '
         f'viewBox="0 0 {W} {Hc}">', DEFS]
    s.append(head(W, Hc, "SECTIONS",
                  "height budget and bolt-station detail \u00b7 all dimensions mm"))
    s.append(f'<line x1="660" y1="96" x2="660" y2="700" stroke="#dde6e8" '
             f'stroke-width="1.5"/>')

    # ---- panel A: bolt station
    cx = 320.0
    s.append(text(60, 118, "Bolt station", size=17, weight="bold"))
    s.append(text(60, 138, f"M6 \u00b7 \u00d8{hole_d:.1f} hole \u00b7 "
                  f"{hex_af:.1f} A/F trap", size=13, fill=DIM))

    cut = 20.0
    b = pad_base_r
    top = boss_d / 2
    solid = [(-cut, 0), (-cut, t), (-b, t), (-top, H), (top, H),
             (b, t), (cut, t), (cut, 0)]
    void = [(-hole_d / 2, 0), (hole_d / 2, 0),
            (hole_d / 2, H - hex_depth), (hex_af / 2, H - hex_depth),
            (hex_af / 2, H), (-hex_af / 2, H), (-hex_af / 2, H - hex_depth),
            (-hole_d / 2, H - hex_depth)]

    def poly(pts, fill, stroke=INK, sw=2.2):
        p = " ".join(f"{cx + x * S:.2f},{zy(z):.2f}" for x, z in pts)
        return f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" ' \
               f'stroke-width="{sw}"/>'

    s.append(poly(solid, FILL))
    s.append(poly(void, "#ffffff", INK, 1.8))

    # base / centre marks
    s.append(f'<line x1="{cx - cut * S}" y1="{zy(0)}" x2="{cx + cut * S}" '
             f'y2="{zy(0)}" stroke="{INK}" stroke-width="2.2"/>')

    # overall height
    s.append(f'<line x1="{cx - cut * S}" y1="{zy(0)}" x2="60" y2="{zy(0)}" '
             f'stroke="{DIM}" stroke-width=".7"/>')
    s.append(f'<line x1="{cx - top * S}" y1="{zy(H)}" x2="60" y2="{zy(H)}" '
             f'stroke="{DIM}" stroke-width=".7"/>')
    s.append(dim_v(60, zy(H), zy(0), f"{H:.1f}", dx=-13))

    # plate thickness (right)
    xd = cx + cut * S + 26
    s.append(f'<line x1="{cx + cut * S}" y1="{zy(0)}" x2="{xd}" y2="{zy(0)}" '
             f'stroke="{DIM}" stroke-width=".7"/>')
    s.append(f'<line x1="{cx + b * S}" y1="{zy(t)}" x2="{xd}" y2="{zy(t)}" '
             f'stroke="{DIM}" stroke-width=".7"/>')
    s.append(dim_v(xd, zy(t), zy(0), f"{t:.1f}", dx=12))

    # (2.5 boss height is the 10.0 overall minus the 7.5 plate)


    # trap depth (inside the open trap so it stays legible)
    xt = cx
    s.append(dim_v(xt, zy(H), zy(H - hex_depth), f"{hex_depth:.1f}", dx=12))

    # trap across flats
    s.append(f'<line x1="{cx - hex_af / 2 * S}" y1="{zy(H)}" '
             f'x2="{cx - hex_af / 2 * S}" y2="{zy(H) - 18}" stroke="{DIM}" '
             f'stroke-width=".7"/>')
    s.append(f'<line x1="{cx + hex_af / 2 * S}" y1="{zy(H)}" '
             f'x2="{cx + hex_af / 2 * S}" y2="{zy(H) - 18}" stroke="{DIM}" '
             f'stroke-width=".7"/>')
    s.append(dim_h(cx - hex_af / 2 * S, cx + hex_af / 2 * S, zy(H) - 26,
                   f"{hex_af:.1f} A/F"))

    # hole
    s.append(f'<line x1="{cx - hole_d / 2 * S}" y1="{zy(0)}" '
             f'x2="{cx - hole_d / 2 * S}" y2="{zy(0) + 16}" stroke="{DIM}" '
             f'stroke-width=".7"/>')
    s.append(f'<line x1="{cx + hole_d / 2 * S}" y1="{zy(0)}" '
             f'x2="{cx + hole_d / 2 * S}" y2="{zy(0) + 16}" stroke="{DIM}" '
             f'stroke-width=".7"/>')
    s.append(dim_h(cx - hole_d / 2 * S, cx + hole_d / 2 * S, zy(0) + 30,
                   f"\u00d8{hole_d:.1f}"))

    # pad callout
    s.append(lead(cx + top * S, zy(H), cx + 172, zy(H) - 56))
    s.append(text(cx + 178, zy(H) - 52,
                  f"\u00d8{boss_d:.0f} pad", size=14, fill=DIM))
    s.append(text(cx + 178, zy(H) - 34,
                  f"({2 * pad_base_r:.1f} at base)", size=13, fill=DIM))

    # labels

    # ---- panel B: plate + rib
    cx = 950.0
    s.append(text(700, 118, "Plate + rib", size=17, weight="bold"))
    s.append(text(700, 138, f"{t:.1f} mm plate + {rib_h:.1f} mm rib = {H:.1f} mm",
                  size=13, fill=DIM))

    cut = 14.0
    rib = [(-cut, 0), (cut, 0), (cut, t), (rib_w / 2, t),
           (rib_top_w / 2, H), (-rib_top_w / 2, H), (-rib_w / 2, t),
           (-cut, t)]

    def poly2(pts, fill, stroke=INK, sw=2.2):
        p = " ".join(f"{cx + x * S:.2f},{zy(z):.2f}" for x, z in pts)
        return f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" ' \
               f'stroke-width="{sw}"/>'

    s.append(poly2(rib, FILL))
    s.append(f'<line x1="{cx - cut * S}" y1="{zy(0)}" x2="{cx + cut * S}" '
             f'y2="{zy(0)}" stroke="{INK}" stroke-width="2.2"/>')

    xd = cx + cut * S + 26
    s.append(f'<line x1="{cx + cut * S}" y1="{zy(0)}" x2="{xd}" y2="{zy(0)}" '
             f'stroke="{DIM}" stroke-width=".7"/>')
    s.append(f'<line x1="{cx + rib_w / 2 * S}" y1="{zy(t)}" x2="{xd}" '
             f'y2="{zy(t)}" stroke="{DIM}" stroke-width=".7"/>')
    s.append(dim_v(xd, zy(t), zy(0), f"{t:.1f}", dx=12))

    # (2.5 rib height is the 10.0 overall minus the 7.5 plate)


    s.append(dim_v(700, zy(H), zy(0), f"{H:.1f}", dx=-12))
    s.append(f'<line x1="{cx - cut * S}" y1="{zy(0)}" x2="700" y2="{zy(0)}" '
             f'stroke="{DIM}" stroke-width=".7"/>')
    s.append(f'<line x1="{cx - rib_top_w / 2 * S}" y1="{zy(H)}" x2="700" y2="{zy(H)}" '
             f'stroke="{DIM}" stroke-width=".7"/>')

    # rib widths
    s.append(dim_h(cx - rib_w / 2 * S, cx + rib_w / 2 * S, zy(0) + 34,
                   f"{rib_w:.1f} base"))
    s.append(dim_h(cx - rib_top_w / 2 * S, cx + rib_top_w / 2 * S, zy(H) - 30,
                   f"{rib_top_w:.1f} top"))

    s.append(text(700, Hc - 46, "Ribs, rim and bolt pads occupy the 2.5 mm above "
                  "the plate;", size=13, fill=DIM))
    s.append(text(700, Hc - 26, "plate carries the bending, so it gets the other "
                  "7.5 mm.", size=13, fill=DIM))
    s.append("</svg>")
    return "\n".join(s)


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "schematic_plan.svg").write_text(plan_svg(), encoding="utf-8")
    (OUT / "schematic_section.svg").write_text(section_svg(), encoding="utf-8")
    print(f"wrote out/schematic_plan.svg  ({board_len:.1f} x {board_wid:.1f} mm)")
    print(f"wrote out/schematic_section.svg  ({H:.1f} mm envelope)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
