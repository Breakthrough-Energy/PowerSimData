import copy


def _check_scale_factors(scale_factors):
    """Validate schema of scale factors dict

    :param dict scale_factors: see :func:`add_electrification`
    """
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
    """Validate schema for zone scaling

    :param powersimdata.input.change_table.ChangeTable obj: change table
    :param dict info: see :func:`add_electrification`
    """
    if not all(isinstance(k, str) for k in info):
        raise ValueError("zone name must be str")
    if all(isinstance(d, dict) for d in info.values()):
        obj._check_zone(info.keys())
    else:
        raise ValueError("zone scaling must be specified via a dict")

    for sf in list(info.values()):
        _check_scale_factors(sf)


def add_electrification(obj, kind, info):
    """Add profiles and scaling factors for electrified demand.

    :param powersimdata.input.change_table.ChangeTable obj: change table
    :param str kind: the kind of demand, e.g. building
    :param dict info: Keys are *'grid'* and *'zone'*, to specify the scale factors in
        the given area. For grid scaling, the value is a *dict*, which maps a *str* to
        *float*. This dict is referred to as *scale_factors* here. The values in
        *scale_factors* must be nonnegative and sum to at most 1. For zone scaling, the
        value is also a *dict*, mapping zone names (*str*) to *scale_factors*.
    """

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
