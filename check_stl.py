#!/usr/bin/env python3
"""Basic STL sanity check: manifoldness, orientation, volume, bounding box."""
import struct
import sys
from collections import defaultdict


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
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
        raise SystemExit("truncated STL")
    tris = []
    for i in range(n):
        off = 84 + i * 50
        vals = struct.unpack("<12fH", raw[off:off + 50])
        tris.append((vals[3:6], vals[6:9], vals[9:12]))
    return tris


def main(path):
    tris = load(path)
    edges = defaultdict(int)
    vol = 0.0
    lo = [1e18] * 3
    hi = [-1e18] * 3
    for a, b, c in tris:
        for p in (a, b, c):
            for k in range(3):
                lo[k] = min(lo[k], p[k])
                hi[k] = max(hi[k], p[k])
        for u, v in ((a, b), (b, c), (c, a)):
            key = tuple(sorted((tuple(round(x, 5) for x in u),
                                tuple(round(x, 5) for x in v))))
            edges[key] += 1
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0

    bad = [e for e, c in edges.items() if c != 2]
    size = [hi[i] - lo[i] for i in range(3)]

    print(f"file        : {path}")
    print(f"triangles   : {len(tris)}")
    print(f"size  XYZ   : {size[0]:.3f} x {size[1]:.3f} x {size[2]:.3f} mm")
    print(f"volume      : {abs(vol)/1000:.2f} cm^3")
    print(f"orientation : {'outward' if vol > 0 else 'INVERTED'}")
    print(f"open/nonmanifold edges: {len(bad)}")
    print("RESULT      :", "OK - watertight" if not bad else "FAIL - not watertight")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
