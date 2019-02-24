#!/usr/bin/env python3

import os.path
import sys
import xml.etree.ElementTree as ET

import svgpathtools
import yaml

import config  # noqa, pylint: disable=unused-import
from util import parse_numeric
from xmlns import INKSCAPE_NS
from xmlns import SVG_NS
from xmlns import XLINK_NS


# monkey-patch svgpathtools.path.scale
_orig_scale = svgpathtools.path.scale


def _my_scale(curve, sx, sy=None, origin=0j):
    try:
        return _orig_scale(curve, sx, sy, origin)
    except Exception as err:
        if err.args != (
                "\nFor `Arc` objects, only scale transforms "
                "with sx==sy are implemented.\n",):
            raise

    assert isinstance(curve, svgpathtools.path.Arc)
    if curve.rotation != 0.0:
        raise Exception("\nFor `Arc` objects with rotation!=0.0, "
                        "only scale transforms with sx==sy are implemented")

    assert sy is not None
    isy = sy * 1j

    def _scale(z):
        return sx * z.real + isy * z.imag

    return svgpathtools.path.Arc(
        start=_scale(curve.start - origin) + origin,
        radius=_scale(curve.radius),
        rotation=curve.rotation,
        large_arc=curve.large_arc,
        sweep=curve.sweep,
        end=_scale(curve.end - origin) + origin)


svgpathtools.path.scale = _my_scale


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


class InterpolateError(ValueError):
    pass


def interpolate_path(path0, path1, interpolator):
    if len(path0) != len(path1):
        raise InterpolateError("number of segments do not match")

    segments = []
    for seg0, seg1 in zip(path0, path1):
        if type(seg0) != type(seg1):  # pylint: disable=unidiomatic-typecheck
            raise InterpolateError("type of segments do not match")

        if svgpathtools.is_bezier_segment(seg0):
            segments.append(svgpathtools.bpoints2bezier([
                interpolator(bp0, bp1)
                for bp0, bp1 in zip(seg0.bpoints(), seg1.bpoints())
            ]))
        elif isinstance(seg0, svgpathtools.Arc):
            if not seg0.rotation == seg1.rotation == 0:
                raise InterpolateError(
                    "cannot interpolate arc segments with rotation")
            if seg0.large_arc != seg1.large_arc or seg0.sweep != seg1.sweep:
                raise InterpolateError("arc segments' flags do not match")

            start = interpolator(seg0.start, seg1.start)
            radius = interpolator(seg0.radius, seg1.radius)
            end = interpolator(seg0.end, seg1.end)
            segments.append(svgpathtools.Arc(
                start=start, radius=radius, rotation=seg0.rotation,
                large_arc=seg0.large_arc, sweep=seg0.sweep, end=end))
        else:
            raise TypeError("unsupported segment type")

    return svgpathtools.Path(*segments)


def interpolate_key(key0, key1, width, height):
    def interpolate_factory():
        width0 = key0["width"]
        height0 = key0["height"]
        width1 = key1["width"]
        height1 = key1["height"]
        # Calculate the plane ax+by+cz=0 that contains three points:
        # (0, 0, 0), (width0, width1, width) and (height0, height1, height).

        # [a, b, c] = [width0, width1, width] x [height0, height1, height]
        a = width1 * height - width * height1
        b = width * height0 - width0 * height
        c = width1 * height0 - width0 * height1

        # Then z=(-a/c)x+(-b/c)y
        c0 = -a / c
        c1 = -b / c
        return lambda x0, x1: x0 * c0 + x1 * c1

    interpolate = interpolate_factory()

    if len(key0["data"]) != len(key1["data"]):
        raise InterpolateError("numbers of lines do not match")

    glyph = []
    for line0, line1 in zip(key0["data"], key1["data"]):
        tokens0 = line0.split()
        tokens1 = line1.split()
        if tokens0[0] != tokens1[0]:
            raise InterpolateError("linetypes do not match")
        linetype = tokens0[0]

        assert linetype in {"use", "rect", "path"}
        if linetype == "use":
            if tokens0[5] != tokens1[5]:
                raise InterpolateError("use names do not match")
            name = tokens0[5]

            x0, y0, width0, height0 = [float(x) for x in tokens0[1:5]]
            x1, y1, width1, height1 = [float(x) for x in tokens1[1:5]]
            glyph.append("use {0} {1} {2} {3} {4}".format(
                interpolate(x0, x1),
                interpolate(y0, y1),
                interpolate(width0, width1),
                interpolate(height0, height1),
                name
            ))
        elif linetype == "rect":
            x0, y0, width0, height0 = [float(x) for x in tokens0[1:]]
            x1, y1, width1, height1 = [float(x) for x in tokens1[1:]]
            glyph.append("rect {0} {1} {2} {3}".format(
                interpolate(x0, x1),
                interpolate(y0, y1),
                interpolate(width0, width1),
                interpolate(height0, height1)
            ))
        elif linetype == "path":
            d0 = " ".join(tokens0[1:])
            d1 = " ".join(tokens1[1:])
            interpolated_d = interpolate_path(
                svgpathtools.parse_path(d0),
                svgpathtools.parse_path(d1),
                interpolate
            ).d()
            glyph.append("path {0}".format(interpolated_d))
    return glyph


def div_inf(x, y):
    try:
        return x / y
    except ValueError:
        if x <= 0:
            raise
        return float("inf")


def interpolate_keys(keys, width, height):
    if len(keys) == 1:
        return keys[0]["data"]
    assert len(keys) >= 2

    t = div_inf(width, height)

    key0, key1 = None, None
    for key0, key1 in zip(keys[:-1], keys[1:]):
        t0 = div_inf(key0["width"], key0["height"])
        t1 = div_inf(key1["width"], key1["height"])
        if t0 <= t <= t1:
            break
    else:
        raise InterpolateError("cannot extrapolate keys")

    if t0 == t:
        return key0["data"]
    if t1 == t:
        return key1["data"]
    assert t0 != t1

    return interpolate_key(key0, key1, width, height)


def normalize_size(width, height):
    assert width > 0 and height > 0
    scale = 360.0 / max(width, height)
    return int(round(scale * width)), int(round(scale * height))


def get_interpolated_data(name, width, height):
    data = load_yaml(name)
    width, height = normalize_size(width, height)
    assert width > 0 and height > 0
    if "keys" not in data or not data["keys"] or width == height:
        return data
    return {
        "name": "{0}-{1}-{2}".format(name, width, height),
        "width": width,
        "height": height,
        "data": interpolate_keys(data["keys"], width, height),
    }


class SVGRenderer(object):
    def __init__(self, expand=False):
        self.expand = expand

        self.name = None
        self.width = None
        self.height = None
        self.rect = None
        self.defs = {}
        self.glyph = None
        self.keys = []

    def render(self, data):
        self.name = data["name"]
        self.width = data["width"]
        self.height = data["height"]
        self.rect = [parse_numeric(x) for x in data["rect"].split()]
        self.glyph = self.render_data(data["data"])
        if not self.expand and "keys" in data:
            self.keys = [self.render_key(key) for key in data["keys"]]
        return self.tosvg()

    def render_key(self, key):
        g_elem = ET.Element(SVG_NS + "g", {
            "id": "key-{0}-{1}".format(key["width"], key["height"]),
            INKSCAPE_NS + "groupmode": "layer",
            "style": "display:none",
        })
        g_elem.extend(self.render_data(key["data"]))
        return g_elem

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
            data = get_interpolated_data(name, width, height)
            glyphdata = resized_glyph(data, width, height, x, y)
            return self.render_data(glyphdata)

        symbol_id = self.require(name, width, height)
        useelem = ET.Element(SVG_NS + "use", {
            "x": "{0}".format(x),
            "y": "{0}".format(y),
            "width": "{0}".format(width),
            "height": "{0}".format(height),
            XLINK_NS + "href": "#{0}".format(symbol_id),
        })
        return [useelem]

    def require(self, name, width=360, height=360):
        data = get_interpolated_data(name, width, height)
        symbol_id = data["name"]
        if symbol_id not in self.defs:
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
        g_elem = ET.Element(SVG_NS + "g", {
            "id": "glyph",
            INKSCAPE_NS + "groupmode": "layer",
        })
        g_elem.append(ET.Element(SVG_NS + "rect", {
            "id": "bbx_rect",
            "x": "{0}".format(self.rect[0]),
            "y": "{0}".format(self.rect[1]),
            "width": "{0}".format(self.rect[2]),
            "height": "{0}".format(self.rect[3]),
            "display": "none",
        }))
        g_elem.extend(self.glyph)
        svg.append(g_elem)
        svg.extend(self.keys)
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
