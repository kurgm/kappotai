#!/usr/bin/env python3

import glob
import os.path
import sys

import yaml


def get_dep_glyphs(data):
    lines = list(data["data"])
    if "keys" in data:
        for key in data["keys"]:
            lines += key["data"]
    glyphs = set()
    for line in lines:
        tokens = line.split()
        if tokens[0] == "use":
            glyphs.add(tokens[5])
    return list(glyphs - {data["name"]})


def mkdeps():
    datadir = os.path.join(os.path.dirname(__file__), "..", "data")
    filelist = glob.glob(os.path.join(datadir, "*.yaml"))
    deplist = []
    for yamlpath in filelist:
        with open(yamlpath) as yamlfile:
            data = yaml.safe_load(yamlfile)
            dep_glyphs = get_dep_glyphs(data)
            if not dep_glyphs:
                continue
            deplist.append("$(DATADIR)/{0} : {1}".format(
                os.path.basename(yamlpath),
                " ".join("$(DATADIR)/{0}.yaml".format(glyph)
                         for glyph in dep_glyphs)
            ))
    header = """\
# Auto generated from scripts/{0}
DATADIR=../data
""".format(os.path.basename(__file__))
    return header + "\n".join(deplist) + "\n"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--outfile", "-o", default=None)

    args = parser.parse_args()

    depsdata = mkdeps()
    if args.outfile is None:
        sys.stdout.write(depsdata)
    else:
        with open(args.outfile, "w") as outfile:
            outfile.write(depsdata)


if __name__ == "__main__":
    main()
