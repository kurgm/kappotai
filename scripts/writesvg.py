#!/usr/bin/env python3

import os.path
import sys
import xml.etree.ElementTree as ET

import svgpathtools
import yaml

import config  # noqa, pylint: disable=unused-import
from util import parse_numeric
from xmlns import SVG_NS
from xmlns import XLINK_NS


def get_yamlpath(name):
    return os.path.join(os.path.dirname(__file__), "..",
                        "data", "{0}.yaml".format(name))


def load_yaml(name):
    with open(get_yamlpath(name)) as yamlfile:
        return yaml.safe_load(yamlfile)


def resized_glyph(data, width, height, dx=0.0, dy=0.0):
    xscale = width / data["width"]
    yscale = height / data["height"]
    glyph = []
    for line in data["data"]:
        tokens = line.split()
        assert tokens[0] in {"use", "rect", "path"}
        if tokens[0] == "use":
            x, y, width, height = [float(x) for x in tokens[1:5]]
            name = tokens[5]
            glyph.append("use {0} {1} {2} {3} {4}".format(
                x * xscale + dx,
                y * yscale + dy,
                width * xscale,
                height * yscale,
                name
            ))
        elif tokens[0] == "rect":
            x, y, width, height = [float(x) for x in tokens[1:]]
            glyph.append("rect {0} {1} {2} {3}".format(
                x * xscale + dx,
                y * yscale + dy,
                width * xscale,
                height * yscale
            ))
        elif tokens[0] == "path":
            d = " ".join(tokens[1:])
            resized_d = (
                svgpathtools.parse_path(d)
                .scaled(xscale, yscale)
                .translated(complex(dx, dy))
            ).d()
            glyph.append("path {0}".format(resized_d))
    return glyph


class SVGRenderer(object):
    def __init__(self, expand=False):
        self.expand = expand

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
        self.glyph = self.render_data(data["data"])
        return self.tosvg()

    def render_data(self, glyphdata):
        elements = []
        for line in glyphdata:
            tokens = line.split()
            assert tokens[0] in {"use", "rect", "path"}
            if tokens[0] == "use":
                x, y, width, height = [parse_numeric(x) for x in tokens[1:5]]
                name = tokens[5]
                elements.extend(self.use(x, y, width, height, name))
            elif tokens[0] == "rect":
                x, y, width, height = [parse_numeric(x) for x in tokens[1:]]
                element = ET.Element(SVG_NS + "rect", {
                    "x": "{0}".format(x),
                    "y": "{0}".format(y),
                    "width": "{0}".format(width),
                    "height": "{0}".format(height),
                })
                elements.append(element)
            elif tokens[0] == "path":
                d = " ".join(tokens[1:])
                element = ET.Element(SVG_NS + "path", {
                    "d": d,
                })
                elements.append(element)
        return elements

    def use(self, x, y, width, height, name):
        if self.expand:
            data = load_yaml(name)
            glyphdata = resized_glyph(data, width, height, x, y)
            return self.render_data(glyphdata)

        symbol_id = self.require(name)
        useelem = ET.Element(SVG_NS + "use", {
            "x": "{0}".format(x),
            "y": "{0}".format(y),
            "width": "{0}".format(width),
            "height": "{0}".format(height),
            XLINK_NS + "href": "#{0}".format(symbol_id),
        })
        return [useelem]

    def require(self, name):
        symbol_id = name
        if symbol_id not in self.defs:
            data = load_yaml(name)
            self.defs[symbol_id] = self.render_symbol(data)
        return symbol_id

    def render_symbol(self, data):
        symbol = ET.Element(SVG_NS + "symbol", {
            "id": data["name"],
            "viewBox": "0 0 {0} {1}".format(data["width"], data["height"]),
            "preserveAspectRatio": "none",
        })
        symbol.extend(self.render_data(data["data"]))
        return symbol

    def tosvg(self):
        svg = ET.Element(SVG_NS + "svg", {
            "id": self.name,
            "width": "{0}".format(self.width),
            "height": "{0}".format(self.height),
            "viewBox": "0 0 {0} {1}".format(self.width, self.height),
            "preserveAspectRatio": "none",
        })
        svg.append(self.render_defs())
        style = ET.Element(SVG_NS + "style")
        with open(os.path.join(os.path.dirname(__file__),
                               "edit.css")) as cssfile:
            style.text = cssfile.read()
        svg.append(style)
        svg.append(ET.Element(SVG_NS + "rect", {
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
        defs = ET.Element(SVG_NS + "defs")
        defs.extend(self.defs.values())
        return defs


def generate_svg(data, *args, **kwargs):
    renderer = SVGRenderer(*args, **kwargs)
    elem = renderer.render(data)
    return ET.tostring(elem, encoding="unicode")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", nargs="?", type=argparse.FileType("r"),
                        default=sys.stdin)
    parser.add_argument("--outfile", "-o", default=None)

    parser.add_argument("--expand", action="store_true")

    args = parser.parse_args()

    indata = yaml.safe_load(args.infile)
    svg = generate_svg(indata, expand=args.expand)
    if args.outfile is None:
        sys.stdout.write(svg)
    else:
        with open(args.outfile, "w") as outfile:
            outfile.write(svg)


if __name__ == "__main__":
    main()
