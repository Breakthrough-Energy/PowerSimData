import copy


def add_electrification(obj, kind, info):
    """TODO"""

    allowed = ["building", "transportation"]
    if kind not in allowed:
        raise ValueError(f"unrecognized class of electrification: {kind}")

    info = copy.deepcopy(info)

    # list of dictionaries, each of which must have scaling factors sum
    # between 0 and 1
    scale_factors = []

    if all(isinstance(k, str) for k in info):
        # scale by zone
        if all(isinstance(d, dict) for d in info.values()):
            obj._check_zone(info.keys())
            scale_factors.extend(info.values())
        # scale entire grid by same factor
        elif all(isinstance(d, (int, float)) for d in info.values()):
            scale_factors.append(info)
        else:
            raise ValueError("unrecognized structure")
    else:
        raise ValueError("unrecognized structure")

    for sf in scale_factors:
        vals = list(sf.values())
        if any(v < 0 for v in vals):
            raise ValueError("scaling factor must be non negative")
        if sum(vals) > 1:
            raise ValueError("scaling factors must sum to between 0 and 1")

    curr = obj.ct.get(kind)
    if curr is None:
        obj.ct[kind] = info
    else:
        obj.ct[kind].update(info)
