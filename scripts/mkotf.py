#!/usr/bin/env python3

import glob
import os.path
import xml.etree.ElementTree as ET

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.transform import Identity
from fontTools.misc.transform import Transform
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib import parse_path
import yaml

import config  # noqa, pylint: disable=unused-import
from xmlns import NSMAP


class Glyph(object):
    def __init__(self, name, d, advwidth, advheight, transform=Identity):
        self.name = name

        advwidth *= abs(transform[0])
        advheight *= abs(transform[3])
        self.advwidth = advwidth
        self.advheight = advheight

        pen = T2CharStringPen(advwidth, None)
        tpen = TransformPen(pen, transform)
        parse_path(d, tpen)
        self.charstring = pen.getCharString()

    def get_hmetrics(self):
        bounds = self.charstring.calcBounds(None)
        if bounds is None:
            return (self.advwidth, 0)
        return (int(self.advwidth), int(bounds[0]))

    def get_vmetrics(self, ascent):
        bounds = self.charstring.calcBounds(None)
        if bounds is None:
            return (self.advheight, ascent)
        return (int(self.advheight), ascent - int(bounds[3]))

    @staticmethod
    def from_svg(svgfile, transform=Identity):
        svg = ET.parse(svgfile).getroot()
        name = svg.get("id")
        return Glyph(
            name=name,
            d=svg.find("svg:path", NSMAP).get("d"),
            advwidth=float(svg.get("width")),
            advheight=float(svg.get("height")),
            transform=transform
        )


def collect_glyphs(srcs, **kwargs):
    glyphs = []
    for src in srcs:
        if os.path.isdir(src):
            files = glob.glob(os.path.join(src, "*.svg"))
        else:
            files = [src]
        for file in files:
            glyphs.append(Glyph.from_svg(file, **kwargs))
    return glyphs


def build_font(srcs, metadata, filename):
    ascent = 880
    descent = 120
    upem = ascent + descent
    scale = upem / 360.0
    transform = Transform(scale, 0, 0, -scale, 0, ascent)
    glyphs = collect_glyphs(srcs, transform=transform)

    builder = FontBuilder(1000, isTTF=False)
    builder.setupGlyphOrder([glyph.name for glyph in glyphs])
    builder.setupCharacterMap({0: ".notdef"})
    psname = metadata["psName"]
    builder.setupCFF(
        psname,
        {"FullName": psname},
        {
            glyph.name: glyph.charstring
            for glyph in glyphs
        },
        {}
    )
    builder.setupHorizontalMetrics({
        glyph.name: glyph.get_hmetrics()
        for glyph in glyphs
    })
    builder.setupHorizontalHeader(ascent=ascent, descent=-descent)
    builder.setupNameTable({})
    builder.setupOS2()
    builder.setupPost()
    builder.setupVerticalMetrics({
        glyph.name: glyph.get_vmetrics(ascent=ascent)
        for glyph in glyphs
    })
    builder.setupVerticalOrigins({}, ascent)
    builder.setupVerticalHeader(ascent=ascent, descent=-descent)
    builder.save(filename)


def main():
    import argparse
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument("src", nargs="+")
    parser.add_argument("--meta", "-m", type=argparse.FileType("r"))
    parser.add_argument("--outfile", "-o", required=True)

    args = parser.parse_args()

    metadata = yaml.safe_load(args.meta)
    build_font(args.src, metadata, args.outfile)


if __name__ == "__main__":
    main()
