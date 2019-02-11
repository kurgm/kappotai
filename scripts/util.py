def parse_numeric(nstr):
    try:
        return int(nstr)
    except ValueError:
        return float(nstr)
