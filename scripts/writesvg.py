#!/usr/bin/env python3

import os.path
import sys
import xml.etree.ElementTree as ET

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

for k, v in _nsmap.items():
    ET.register_namespace(k, v)

ET.register_namespace("", _SVG_NS[1:-1])


class SVGRenderer(object):
    def __init__(self):
        self.name = None
        self.width = None
        self.height = None
        self.rect = None
        self.defs = {}
        self.glyph = None

    def render(self, data):
        self.name = data["name"]
        self.width = data["width"]
        self.height = data["height"]
        self.rect = [parse_numeric(x) for x in data["rect"].split()]
        self.glyph = self.render_data(data)
        return self.tosvg()

    def render_data(self, data):
        elements = []
        for line in data["data"]:
            tokens = line.split()
            assert tokens[0] in {"use", "rect", "path"}
            if tokens[0] == "use":
                x, y, width, height = [parse_numeric(x) for x in tokens[1:5]]
                name = tokens[5]
                symbol_id = self.require(name)
                element = ET.Element(_SVG_NS + "use", {
                    "x": "{0}".format(x),
                    "y": "{0}".format(y),
                    "width": "{0}".format(width),
                    "height": "{0}".format(height),
                    _XLINK_NS + "href": "#{0}".format(symbol_id),
                })
                elements.append(element)
            elif tokens[0] == "rect":
                x, y, width, height = [parse_numeric(x) for x in tokens[1:]]
                element = ET.Element(_SVG_NS + "rect", {
                    "x": "{0}".format(x),
                    "y": "{0}".format(y),
                    "width": "{0}".format(width),
                    "height": "{0}".format(height),
                })
                elements.append(element)
            elif tokens[0] == "path":
                d = " ".join(tokens[1:])
                element = ET.Element(_SVG_NS + "path", {
                    "d": d,
                })
                elements.append(element)
        return elements

    def require(self, name):
        symbol_id = name
        if symbol_id not in self.defs:
            filepath = os.path.join(os.path.dirname(__file__), "..",
                                    "data", "{0}.yaml".format(name))
            with open(filepath) as infile:
                data = yaml.safe_load(infile)
            self.defs[symbol_id] = self.render_symbol(data)
        return symbol_id

    def render_symbol(self, data):
        symbol = ET.Element(_SVG_NS + "symbol", {
            "id": data["name"],
            "viewBox": "0 0 {0} {1}".format(data["width"], data["height"]),
            "preserveAspectRatio": "none",
        })
        symbol.extend(self.render_data(data))
        return symbol

    def tosvg(self):
        svg = ET.Element(_SVG_NS + "svg", {
            "id": self.name,
            "width": "{0}".format(self.width),
            "height": "{0}".format(self.height),
            "viewBox": "0 0 {0} {1}".format(self.width, self.height),
            "preserveAspectRatio": "none",
        })
        svg.append(self.render_defs())
        style = ET.Element(_SVG_NS + "style")
        with open(os.path.join(os.path.dirname(__file__),
                               "edit.css")) as cssfile:
            style.text = cssfile.read()
        svg.append(style)
        svg.append(ET.Element(_SVG_NS + "rect", {
            "id": "bbx_rect",
            "x": "{0}".format(self.rect[0]),
            "y": "{0}".format(self.rect[1]),
            "width": "{0}".format(self.rect[2]),
            "height": "{0}".format(self.rect[3]),
            "display": "none",
        }))
        svg.extend(self.glyph)
        return svg

    def render_defs(self):
        defs = ET.Element(_SVG_NS + "defs")
        defs.extend(self.defs.values())
        return defs


def generate_svg(data):
    renderer = SVGRenderer()
    elem = renderer.render(data)
    return ET.tostring(elem, encoding="unicode")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", nargs="?", type=argparse.FileType("r"),
                        default=sys.stdin)
    parser.add_argument("--outfile", "-o", default=None)

    args = parser.parse_args()

    indata = yaml.safe_load(args.infile)
    svg = generate_svg(indata)
    if args.outfile is None:
        sys.stdout.write(svg)
    else:
        with open(args.outfile, "w") as outfile:
            outfile.write(svg)


if __name__ == "__main__":
    main()
