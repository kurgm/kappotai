#!/usr/bin/env python3

from collections import defaultdict
import sys

from fontTools.ttLib import TTFont


class VMTXFeatureGenerator(object):
    def __init__(self):
        self.mtx = {}

    def import_font(self, font, cidmap):
        upem = font["head"].unitsPerEm
        vmetrics = font["vmtx"].metrics
        vorgrecs = font["VORG"].VOriginRecords
        names = set(font.getGlyphOrder()) & cidmap.keys()
        for name in names:
            cids = cidmap[name]
            vadv, _tsb = vmetrics[name]
            if vadv == upem:
                vadv = None
            if name in vorgrecs:
                vorg = vorgrecs[name]
            else:
                vorg = None
            for cid in cids:
                self.mtx[cid] = (vadv, vorg)

    def generate(self):
        lines = []
        lines.append("table vmtx {")
        lines.extend(
            line
            for cid, (vadv, vorg) in self.mtx.items()
            for line in [
                "  VertOriginY \\{0:05d} {1};".format(cid, vorg)
                if vorg is not None else None,
                "  VertAdvanceY \\{0:05d} {1};".format(cid, vadv)
                if vadv is not None else None,
            ] if line
        )
        lines.append("} vmtx;")
        return "\n".join(lines) + "\n"


def parse_map(mappath):
    cidmap = defaultdict(list)
    with open(mappath) as mapfile:
        next(mapfile)  # skip "mergefonts"
        for line in mapfile:
            cid, name = line.split()
            cidmap[name].append(int(cid))
    return cidmap


def mkvmtxfeat(infiles):
    gen = VMTXFeatureGenerator()
    for mapfile, fontfile in infiles:
        cidmap = parse_map(mapfile)
        gen.import_font(TTFont(fontfile), cidmap)
    return gen.generate()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--outfile", "-o")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    if len(args.files) % 2 != 0:
        raise ValueError("number of files must be even")
    maps = args.files[::2]
    fonts = args.files[1::2]

    featdata = mkvmtxfeat(zip(maps, fonts))
    if args.outfile is None:
        sys.stdout.write(featdata)
    else:
        with open(args.outfile, "w") as outfile:
            outfile.write(featdata)


if __name__ == "__main__":
    main()
