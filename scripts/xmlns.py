import xml.etree.ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK_NS = "{http://www.w3.org/1999/xlink}"
INKSCAPE_NS = "{http://www.inkscape.org/namespaces/inkscape}"
SODIPODI_NS = "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}"

NSMAP = {
    "svg": SVG_NS[1:-1],
    "xlink": XLINK_NS[1:-1],
    "inkscape": INKSCAPE_NS[1:-1],
    "sodipodi": SODIPODI_NS[1:-1],
}

for k, v in NSMAP.items():
    ET.register_namespace(k, v)

ET.register_namespace("", SVG_NS[1:-1])
