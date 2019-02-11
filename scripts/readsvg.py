#!/usr/bin/env python3

import sys

from lxml import etree as ET
import yaml

import config  # noqa, pylint: disable=unused-import
from util import parse_numeric

_SVG_NS = "{http://www.w3.org/2000/svg}"
_XLINK_NS = "{http://www.w3.org/1999/xlink}"
_INKSCAPE_NS = "{http://www.inkscape.org/namespaces/inkscape}"
_SODIPODI_NS = "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}"

_nsmap = {
    "svg": _SVG_NS[1:-1],
    "xlink": _XLINK_NS[1:-1],
    "inkscape": _INKSCAPE_NS[1:-1],
    "sodipodi": _SODIPODI_NS[1:-1],
}


def readsvg(svgfile):
    svg = ET.parse(svgfile).getroot()

    svg.remove(svg.find("svg:defs", _nsmap))

    bbx_rect = svg.find("svg:rect[@id='bbx_rect']", _nsmap)
    rectstr = "{0} {1} {2} {3}".format(
        bbx_rect.get("x"),
        bbx_rect.get("y"),
        bbx_rect.get("width"),
        bbx_rect.get("height")
    )
    svg.remove(bbx_rect)

    glyph = []
    for elem in svg.xpath(".//svg:use|.//svg:rect|.//svg:path",
                          namespaces=_nsmap):
        if elem.tag == _SVG_NS + "use":
            name = elem.get(_XLINK_NS + "href")[1:]
            glyph.append("use {0} {1} {2} {3} {4}".format(
                elem.get("x"),
                elem.get("y"),
                elem.get("width"),
                elem.get("height"),
                name
            ))
        elif elem.tag == _SVG_NS + "rect":
            glyph.append("rect {0} {1} {2} {3}".format(
                elem.get("x"),
                elem.get("y"),
                elem.get("width"),
                elem.get("height")
            ))
        elif elem.tag == _SVG_NS + "path":
            glyph.append("path {0}".format(elem.get("d")))

    return {
        "name": svg.get("id"),
        "width": parse_numeric(svg.get("width")),
        "height": parse_numeric(svg.get("height")),
        "rect": rectstr,
        "data": glyph,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", nargs="?", type=argparse.FileType("r"),
                        default=sys.stdin)
    parser.add_argument("--outfile", "-o", default=None)

    args = parser.parse_args()

    data = readsvg(args.infile)
    yamldata = yaml.dump(data, default_flow_style=False)
    if args.outfile is None:
        sys.stdout.write(yamldata)
    else:
        with open(args.outfile, "w") as outfile:
            outfile.write(yamldata)


if __name__ == "__main__":
    main()
