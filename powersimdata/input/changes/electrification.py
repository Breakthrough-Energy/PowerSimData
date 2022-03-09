import copy


def _check_scale_factors(scale_factors):
    for sf in scale_factors:
        vals = list(sf.values())
        if any(v < 0 for v in vals):
            raise ValueError("scaling factor must be non negative")
        if sum(vals) > 1:
            raise ValueError("scaling factors must sum to between 0 and 1")


def _check_zone_scaling(obj, info):
    if not all(isinstance(k, str) for k in info):
        raise ValueError("unrecognized structure")
    if all(isinstance(d, dict) for d in info.values()):
        obj._check_zone(info.keys())
    _check_scale_factors(list(info.values()))


def _check_grid_scaling(info):
    if not all(isinstance(k, str) for k in info):
        raise ValueError("keys must be str")
    if not all(isinstance(d, (int, float)) for d in info.values()):
        raise ValueError("scale factors must be numeric")
    _check_scale_factors([info])


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
    _check_grid_scaling(grid)

    curr = obj.ct.get(kind)
    if curr is None:
        obj.ct[kind] = {"grid": {}, "zone": {}}
    obj.ct[kind]["grid"].update(grid)
    obj.ct[kind]["zone"].update(zone)
