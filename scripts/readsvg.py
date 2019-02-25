#!/usr/bin/env python3

import sys

from lxml import etree as ET
import yaml

import config  # noqa, pylint: disable=unused-import
from util import parse_numeric
from xmlns import NSMAP
from xmlns import SVG_NS
from xmlns import XLINK_NS


def get_glyph(elems):
    glyph = []
    for elem in elems:
        if elem.tag == SVG_NS + "use":
            name = elem.get(XLINK_NS + "href")[1:].split("-")[0]
            glyph.append("use {0} {1} {2} {3} {4}".format(
                elem.get("x"),
                elem.get("y"),
                elem.get("width"),
                elem.get("height"),
                name
            ))
        elif elem.tag == SVG_NS + "rect":
            glyph.append("rect {0} {1} {2} {3}".format(
                elem.get("x"),
                elem.get("y"),
                elem.get("width"),
                elem.get("height")
            ))
        elif elem.tag == SVG_NS + "path":
            glyph.append("path {0}".format(elem.get("d")))
    return glyph


def readsvg(svgfile):
    svg = ET.parse(svgfile).getroot()

    svg.remove(svg.find("svg:defs", NSMAP))

    bbx_rect = svg.find(".//svg:rect[@id='bbx_rect']", NSMAP)
    rectstr = "{0} {1} {2} {3}".format(
        bbx_rect.get("x"),
        bbx_rect.get("y"),
        bbx_rect.get("width"),
        bbx_rect.get("height")
    )
    bbx_rect.getparent().remove(bbx_rect)

    keys = []
    for elem in svg.xpath("./svg:g[starts-with(@id, 'key-')]",
                          namespaces=NSMAP):
        _num, keyw, keyh = elem.get("id")[len("key-"):].split("-")
        keys.append({
            "width": parse_numeric(keyw),
            "height": parse_numeric(keyh),
            "data": get_glyph(elem.xpath(".//svg:use|.//svg:rect|.//svg:path",
                                         namespaces=NSMAP)),
        })
        svg.remove(elem)

    glyph = get_glyph(svg.xpath(".//svg:use|.//svg:rect|.//svg:path",
                                namespaces=NSMAP))

    data = {
        "name": svg.get("id"),
        "width": parse_numeric(svg.get("width")),
        "height": parse_numeric(svg.get("height")),
        "rect": rectstr,
        "data": glyph,
    }
    if keys:
        data["keys"] = keys
    return data


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
