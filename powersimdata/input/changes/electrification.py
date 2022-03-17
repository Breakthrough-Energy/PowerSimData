import copy
from dataclasses import dataclass
from typing import Dict


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


@dataclass
class ScaleFactors:
    """Map profile to adoption"""

    sf: Dict[str, float]

    def value(self):
        return self.sf

    @staticmethod
    def from_dict(scale_factors):
        _check_scale_factors(scale_factors)
        return ScaleFactors(sf=scale_factors)


@dataclass
class AreaScaling:
    """Map end uses to adoption rates of each technology"""

    end_uses: Dict[str, ScaleFactors]

    def value(self):
        return {k: v.value() for k, v in self.end_uses.items()}

    @staticmethod
    def from_dict(info):
        if not isinstance(info, dict):
            raise ValueError("scale factors must be a dict")
        if not all(isinstance(k, str) for k in info):
            raise ValueError("end use must be str")
        end_uses = {k: ScaleFactors.from_dict(v) for k, v in info.items()}
        return AreaScaling(end_uses=end_uses)


@dataclass
class ElectrifiedDemand:
    grid_info: AreaScaling
    zone_info: Dict[str, AreaScaling]

    def value(self):
        zones = {k: v.value() for k, v in self.zone_info.items()}
        return {"grid": self.grid_info.value(), "zone": zones}

    @staticmethod
    def from_dict(obj, info):
        if not isinstance(info, dict):
            raise ValueError("info must be a dict")
        grid = info.get("grid", {})
        grid_info = AreaScaling.from_dict(grid)

        zone = info.get("zone", {})
        if not all(isinstance(k, str) for k in zone):
            raise ValueError("zone name must be str")
        obj._check_zone(list(zone.keys()))

        zone_info = {k: AreaScaling.from_dict(v) for k, v in zone.items()}
        return ElectrifiedDemand(grid_info=grid_info, zone_info=zone_info)


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

    result = ElectrifiedDemand.from_dict(obj, info).value()

    curr = obj.ct.get(kind)
    if curr is None:
        obj.ct[kind] = {"grid": {}, "zone": {}}
    obj.ct[kind]["grid"].update(result["grid"])
    obj.ct[kind]["zone"].update(result["zone"])
