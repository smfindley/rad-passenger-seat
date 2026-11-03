#!/usr/bin/env python3
"""Convert a binary STL to a 3MF (3D Manufacturing Format) core-spec model.

Writes a plain, standards-compliant 3MF: [Content_Types].xml, _rels/.rels and
3D/3dmodel.model. No slicer-specific metadata, so OrcaSlicer (and Flash Studio,
Bambu, Prusa) all import it as geometry.

The model is centred on the XY origin, which is where Orca's printable area
(roughly -110..110 for a 220 mm bed) is centred, and sits with Z=0 on the bed.

Usage: make_3mf.py in.stl out.3mf [--title "..."] [--desc "..."]
"""
import os
import struct
import sys
import zipfile
import zlib
from xml.sax.saxutils import escape

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""


def read_stl(path):
    raw = open(path, "rb").read()
    if raw[:5].lower().startswith(b"solid") and b"facet" in raw[:2000]:
        tris, cur = [], []
        for line in raw.decode("ascii", "replace").splitlines():
            p = line.split()
            if p and p[0] == "vertex":
                cur.append(tuple(float(x) for x in p[1:4]))
                if len(cur) == 3:
                    tris.append(tuple(cur))
                    cur = []
        return tris
    n = struct.unpack("<I", raw[80:84])[0]
    if len(raw) != 84 + n * 50:
        raise SystemExit(f"{path}: truncated binary STL")
    tris = []
    for i in range(n):
        off = 84 + i * 50
        v = struct.unpack("<12f", raw[off:off + 48])
        tris.append((v[3:6], v[6:9], v[9:12]))
    return tris


def quant(p, q=1e-5):
    return (round(p[0] / q), round(p[1] / q), round(p[2] / q))


def build(tris, dx, dy):
    index = {}
    verts = []
    faces = []
    for tri in tris:
        face = []
        for p in tri:
            p = (p[0] + dx, p[1] + dy, p[2])
            k = quant(p)
            i = index.get(k)
            if i is None:
                i = len(verts)
                index[k] = i
                verts.append(p)
            face.append(i)
        if len(set(face)) == 3:
            faces.append(face)
    return verts, faces


def fmt(x):
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def model_xml(title, desc, name, verts, faces):
    v = "".join(f'<vertex x="{fmt(p[0])}" y="{fmt(p[1])}" z="{fmt(p[2])}"/>' for p in verts)
    f = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
        f' <metadata name="Title">{escape(title)}</metadata>\n'
        f' <metadata name="Description">{escape(desc)}</metadata>\n'
        ' <metadata name="Application">make_3mf.py</metadata>\n'
        ' <resources>\n'
        f'  <object id="1" type="model" name="{escape(name)}">\n'
        f'   <mesh><vertices>{v}</vertices><triangles>{f}</triangles></mesh>\n'
        '  </object>\n'
        ' </resources>\n'
        ' <build><item objectid="1"/></build>\n'
        '</model>\n'
    )


def volume(verts, faces):
    vol = 0.0
    for a, b, c in faces:
        p, q, r = verts[a], verts[b], verts[c]
        vol += (p[0] * (q[1] * r[2] - q[2] * r[1])
                - p[1] * (q[0] * r[2] - q[2] * r[0])
                + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6.0
    return vol


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    src, dst = argv[1], argv[2]
    title = "RAD passenger seat base board"
    desc = ""
    for i, a in enumerate(argv):
        if a == "--title" and i + 1 < len(argv):
            title = argv[i + 1]
        if a == "--desc" and i + 1 < len(argv):
            desc = argv[i + 1]

    tris = read_stl(src)
    xs = [p[0] for t in tris for p in t]
    ys = [p[1] for t in tris for p in t]
    dx = -(max(xs) + min(xs)) / 2
    dy = -(max(ys) + min(ys)) / 2

    verts, faces = build(tris, dx, dy)
    xml = model_xml(title, desc, os.path.splitext(os.path.basename(src))[0], verts, faces)

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", xml)

    # ---- validate what actually landed on disk -----------------------
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(dst) as z:
        bad = z.testzip()
        if bad:
            raise SystemExit(f"zip corrupt at {bad}")
        names = set(z.namelist())
        for need in ("[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model"):
            if need not in names:
                raise SystemExit(f"missing {need}")
        root = ET.fromstring(z.read("3D/3dmodel.model"))

    ns = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"
    assert root.get("unit") == "millimeter", "unit must be millimetre"
    rv, rf = [], []
    for e in root.iter(ns + "vertex"):
        rv.append((float(e.get("x")), float(e.get("y")), float(e.get("z"))))
    for e in root.iter(ns + "triangle"):
        rf.append((int(e.get("v1")), int(e.get("v2")), int(e.get("v3"))))

    assert len(rf) == len(faces), "triangle count changed on rewrite"
    assert max(max(f) for f in rf) < len(rv), "index out of range"
    vol_out = volume(rv, rf)
    vol_in = volume([p for t in tris for p in t],
                    [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(tris))])

    bx = [p[0] for p in rv]; by = [p[1] for p in rv]; bz = [p[2] for p in rv]
    print(f"{dst}")
    print(f"  bytes        : {os.path.getsize(dst)}")
    print(f"  vertices     : {len(rv)}  (dedup from {len(tris) * 3})")
    print(f"  triangles    : {len(rf)}")
    print(f"  bbox         : {max(bx)-min(bx):.2f} x {max(by)-min(by):.2f} x {max(bz)-min(bz):.2f} mm")
    print(f"  centred at   : x {(max(bx)+min(bx))/2:+.3f}  y {(max(by)+min(by))/2:+.3f}  z {min(bz):.3f}")
    print(f"  volume       : {vol_out/1000:.2f} cm^3  (stl {vol_in/1000:.2f})")
    if abs(vol_out - vol_in) > 1.0:
        raise SystemExit("volume mismatch after conversion")
    print("  RESULT       : OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
