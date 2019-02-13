#!/usr/bin/env python3

import glob
import os.path
import re
import xml.etree.ElementTree as ET

from fontTools.fontBuilder import FontBuilder
from fontTools.misc.transform import Identity
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib import parse_path
import yaml

import config  # noqa, pylint: disable=unused-import
from xmlns import NSMAP


class Glyph(object):
    def __init__(self, name, d, unicode, advwidth, transform=Identity):
        self.name = name
        self.unicode = unicode

        advwidth, _ = transform.transformPoint((advwidth, 0))
        self.advwidth = advwidth

        pen = T2CharStringPen(advwidth, None)
        tpen = TransformPen(pen, transform)
        parse_path(d, tpen)
        self.charstring = pen.getCharString()

    def get_hmetrics(self):
        bounds = self.charstring.calcBounds(None)
        if bounds is None:
            return (self.advwidth, 0)
        return (int(self.advwidth), int(bounds[0]))


def unicode_from_name(name):
    assert re.match("^u[0-9a-f]{4,5}$", name)
    return int(name[1:], 16)


def glyph_from_svg(svgfile, transform=Identity):
    svg = ET.parse(svgfile).getroot()
    name = svg.get("id")
    return Glyph(
        name=name,
        d=svg.find("svg:path", NSMAP).get("d"),
        unicode=unicode_from_name(name),
        advwidth=float(svg.get("width")),
        transform=transform
    )


def default_glyphs():
    return [
        Glyph(
            name=".notdef",
            d="M 100 -100 H 924 V 724 H 100 Z M 110 -90 V 714 H 914 V -90 Z",
            unicode=None,
            advwidth=1024,
        ),
        Glyph(
            name=".null",
            d="",
            unicode=0,
            advwidth=0,
        ),
    ]


def collect_glyphs(srcdir, **kwargs):
    glyphs = default_glyphs()
    files = glob.glob(os.path.join(srcdir, "*.svg"))
    for file in files:
        glyphs.append(glyph_from_svg(file, **kwargs))
    return glyphs


def get_fontbbx(glyphs):
    bpen = BoundsPen(None)
    for glyph in glyphs:
        glyph.charstring.draw(bpen)
    return bpen.bounds


def build_font(srcdir, metadata, filename):
    scale = 1024.0 / 360.0
    descent = 200
    transform = Transform(scale, 0, 0, -scale, 0, 1024.0 - descent)
    glyphs = collect_glyphs(srcdir, transform=transform)

    builder = FontBuilder(1024, isTTF=False)
    builder.setupGlyphOrder([glyph.name for glyph in glyphs])
    builder.setupCharacterMap({
        glyph.unicode: glyph.name
        for glyph in glyphs
        if glyph.unicode is not None
    })
    psname = metadata["nameStrings"]["psName"]["en"]
    builder.setupCFF(
        psname,
        {"FullName": psname},
        {
            glyph.name: glyph.charstring
            for glyph in glyphs
        },
        {}
    )
    metrics = {
        glyph.name: glyph.get_hmetrics()
        for glyph in glyphs
    }
    fontbbx = get_fontbbx(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=1024 - descent, descent=-descent)
    builder.setupNameTable(metadata["nameStrings"])
    builder.setupOS2(
        sTypoAscender=1024 - descent,
        sTypoDescender=-descent,
        usWinAscent=fontbbx[3],
        usWinDescent=-fontbbx[1],
    )
    builder.setupPost()
    builder.save(filename)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("meta", type=argparse.FileType("r"))
    parser.add_argument("--outfile", "-o", required=True)

    args = parser.parse_args()

    metadata = yaml.safe_load(args.meta)
    build_font(args.src, metadata, args.outfile)


if __name__ == "__main__":
    main()
