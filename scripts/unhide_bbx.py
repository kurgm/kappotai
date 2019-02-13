#!/usr/bin/env python3

import sys
import xml.etree.ElementTree as ET

import config  # noqa, pylint: disable=unused-import
from xmlns import NSMAP


def unhide_bbx(svgfile):
    svg = ET.parse(svgfile).getroot()
    bbx_rect = svg.find("svg:rect[@id='bbx_rect']", NSMAP)
    bbx_rect.set("display", "inline")
    return ET.tostring(svg, encoding="unicode")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", nargs="?", type=argparse.FileType("r"),
                        default=sys.stdin)
    parser.add_argument("--outfile", "-o", default=None)

    args = parser.parse_args()

    svg = unhide_bbx(args.infile)
    if args.outfile is None:
        sys.stdout.write(svg)
    else:
        with open(args.outfile, "w") as outfile:
            outfile.write(svg)


if __name__ == "__main__":
    main()
