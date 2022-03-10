import copy


def _check_scale_factors(scale_factors):
    if not all(isinstance(k, str) for k in scale_factors):
        raise ValueError("profile name must be str")
    if not all(isinstance(d, (int, float)) for d in scale_factors.values()):
        raise ValueError("scale factors must be numeric")
    vals = list(scale_factors.values())
    if any(v < 0 for v in vals):
        raise ValueError("scaling factor must be non negative")
    if sum(vals) > 1:
        raise ValueError("scaling factors must sum to between 0 and 1")


def _check_zone_scaling(obj, info):
    if not all(isinstance(k, str) for k in info):
        raise ValueError("zone name must be str")
    if all(isinstance(d, dict) for d in info.values()):
        obj._check_zone(info.keys())
    else:
        raise ValueError("zone scaling must be specified via a dict")

    for sf in list(info.values()):
        _check_scale_factors(sf)


def add_electrification(obj, kind, info):
    """TODO"""

    allowed = ["building", "transportation"]
    if kind not in allowed:
        raise ValueError(f"unrecognized class of electrification: {kind}")

    info = copy.deepcopy(info)

    if not set(info) <= {"zone", "grid"}:
        raise ValueError("unrecognized scaling key")

    zone = info.get("zone", {})
    grid = info.get("grid", {})
    _check_zone_scaling(obj, zone)
    _check_scale_factors(grid)

    curr = obj.ct.get(kind)
    if curr is None:
        obj.ct[kind] = {"grid": {}, "zone": {}}
    obj.ct[kind]["grid"].update(grid)
    obj.ct[kind]["zone"].update(zone)
