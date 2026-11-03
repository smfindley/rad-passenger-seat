#!/usr/bin/env python3
"""Strip non-essential chunks from OpenSCAD's PNG renders.

OpenSCAD 2026.10 writes an eXIf metadata chunk into every PNG. It is legal
PNG, but several viewers, validators and image proxies choke on it, so the
file gets reported as corrupt. This rewrites each PNG with only the chunks
needed to decode it (IHDR, sRGB, IDAT, IEND), leaving the pixels untouched.

Usage: clean_png.py out/*.png
"""
import glob
import struct
import sys
import zlib

KEEP = {b"IHDR", b"sRGB", b"gAMA", b"IDAT", b"IEND", b"PLTE", b"tRNS"}

# filter-byte sanity: 0..4 only
FMT_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def clean(path, dry_run=False):
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path}: not a PNG")

    out = bytearray(data[:8])
    pos = 8
    removed = []
    ihdr = idat = None
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        crc_at = pos + 8 + length
        if crc_at + 4 > len(data):
            raise SystemExit(f"{path}: truncated {ctype!r} chunk")
        stored = struct.unpack(">I", data[crc_at:crc_at + 4])[0]
        if stored != zlib.crc32(ctype + body) & 0xFFFFFFFF:
            raise SystemExit(f"{path}: bad CRC in {ctype!r}")
        whole = data[pos:crc_at + 4]
        pos = crc_at + 4

        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        if ctype == b"IDAT":
            idat = (idat or b"") + body

        if ctype in KEEP:
            out += whole
        else:
            removed.append(f"{ctype.decode('latin1')}({length})")
        if ctype == b"IEND":
            break

    # sanity: decode the pixel stream and check the filter bytes
    w, h, bd, ct, comp, filt, inter = ihdr
    if (bd, comp, filt, inter) != (8, 0, 0, 0):
        raise SystemExit(f"{path}: unexpected IHDR {ihdr}")
    raw = zlib.decompress(idat)
    stride = w * FMT_CHANNELS[ct]
    if len(raw) != h * (1 + stride):
        raise SystemExit(f"{path}: scanline length mismatch")
    for y in range(h):
        if raw[y * (1 + stride)] > 4:
            raise SystemExit(f"{path}: invalid filter byte on row {y}")

    if dry_run:
        return removed, len(out)

    with open(path, "wb") as f:
        f.write(out)
    return removed, len(out)


def main(argv):
    targets = []
    for a in argv[1:]:
        targets.extend(sorted(glob.glob(a)) if any(c in a for c in "*?[") else [a])
    if not targets:
        raise SystemExit(__doc__)
    for p in targets:
        try:
            removed, size = clean(p)
        except Exception as e:  # noqa: BLE001
            print(f"FAILED  {p}: {e}")
            return 1
        print(f"ok      {p}  {size} bytes  removed: {', '.join(removed) or 'nothing'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
