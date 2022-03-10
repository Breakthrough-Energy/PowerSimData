import pytest

from powersimdata.input.change_table import ChangeTable
from powersimdata.input.changes.electrification import (
    _check_scale_factors,
    _check_zone_scaling,
    add_electrification,
)
from powersimdata.input.grid import Grid


def test_check_zone():
    obj = ChangeTable(Grid("Texas"))
    info = {"Coast": {"standard_heat_pump_v1": 0.2}}
    _check_zone_scaling(obj, info)

    with pytest.raises(ValueError):
        info = {"Maine": {"standard_heat_pump_v1": 0.2}}
        _check_zone_scaling(obj, info)


def test_check_scale_factors():
    with pytest.raises(ValueError):
        info = {"tech1": "foo"}
        _check_scale_factors(info)

    info = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": -3}
    with pytest.raises(ValueError):
        _check_scale_factors(info)

    with pytest.raises(ValueError):
        info = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": 0.8}
        _check_scale_factors(info)


def test_add_electrification():
    obj = ChangeTable(Grid("Texas"))
    kind = "building"

    info = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": 0.3}
    add_electrification(obj, kind, {"grid": info})

    with pytest.raises(ValueError):
        add_electrification(obj, "foo", {"grid": info})


def test_add_electrification_by_zone():
    obj = ChangeTable(Grid("Eastern"))
    kind = "building"

    info = {
        "New York City": {"advanced_heat_pump_v2": 0.7},
        "Western North Carolina": {
            "standard_heat_pump_v1": 0.5,
            "advanced_heat_pump_v2": 0.5,
        },
    }
    add_electrification(obj, kind, {"zone": info})

    info = {"Maine": {"standard_heat_pump_v1": 0.2, "advanced_heat_pump_v2": 0.8}}
    add_electrification(obj, kind, {"zone": info})

    result = obj.ct[kind]
    assert "Maine" in result["zone"]
    assert "New York City" in result["zone"]


def test_add_electrification_combined():
    obj = ChangeTable(Grid("Eastern"))
    kind = "building"

    zone = {"Maine": {"standard_heat_pump_v1": 0.2, "advanced_heat_pump_v2": 0.8}}
    grid = {"standard_heat_pump_v1": 0.7}
    add_electrification(obj, kind, {"grid": grid, "zone": zone})

    result = obj.ct[kind]
    assert "Maine" in result["zone"]
    assert "standard_heat_pump_v1" in result["grid"]
