#!/usr/bin/env python3

from functools import wraps
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


def get_dep_map():
    datadir = os.path.join(os.path.dirname(__file__), "..", "data")
    filelist = glob.glob(os.path.join(datadir, "*.yaml"))
    depmap = {}
    for yamlpath in filelist:
        with open(yamlpath) as yamlfile:
            data = yaml.safe_load(yamlfile)
            dep_glyphs = get_dep_glyphs(data)
            depmap[data["name"]] = dep_glyphs
    return depmap


def memoize(func):
    memo = {}
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args in memo:
            return memo[args]
        result = func(*args, **kwargs)
        memo[args] = result
        return result
    return wrapper


@memoize
def sub_dependents(name, depmap):
    result = set(depmap[name])
    for dependent in depmap[name]:
        result.update(sub_dependents(dependent, depmap=depmap))
    return result


def get_dep_list(depmap):
    for name in depmap.keys():
        subdep = sub_dependents(name, depmap=depmap)
        if not subdep:
            continue
        yield "edit/{0}.svg build/expand/{0}.svg : {1}".format(
            name,
            " ".join("data/{0}.yaml".format(dep)
                     for dep in subdep)
        )


def mkdeps():
    depmap = get_dep_map()
    deplist = get_dep_list(depmap)
    header = """\
# Auto generated from scripts/{0}
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
