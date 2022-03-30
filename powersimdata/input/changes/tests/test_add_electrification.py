import pytest

from powersimdata.input.change_table import ChangeTable
from powersimdata.input.changes.electrification import (
    AreaScaling,
    ScaleFactors,
    _check_scale_factors,
    add_electrification,
)
from powersimdata.input.grid import Grid


def test_scale_factors():
    info = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": -3}

    invalid = (info, [1, 2, 3], {123: 456}, {"foo": "bar"})
    for arg in invalid:
        with pytest.raises(ValueError):
            ScaleFactors(arg)

    info["advanced_heat_pump_v2"] = 0.3
    result = ScaleFactors(info)
    assert info == result.value()


def test_area_scaling():
    with pytest.raises(ValueError):
        AreaScaling([])
    with pytest.raises(ValueError):
        AreaScaling({1: 2})

    sf = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": 0.2}
    info = {"res_heating": sf}
    result = AreaScaling(info)
    assert info == result.value()


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

    sf = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": 0.3}
    info = {"res_heating": sf}
    add_electrification(obj, kind, {"grid": info})

    with pytest.raises(ValueError):
        add_electrification(obj, "foo", {"grid": info})


def test_add_electrification_by_zone():
    obj = ChangeTable(Grid("Eastern"))
    kind = "building"

    info = {
        "New York City": {"res_cooking": {"advanced_heat_pump_v2": 0.7}},
        "Western North Carolina": {
            "com_hot_water": {
                "standard_heat_pump_v1": 0.5,
                "advanced_heat_pump_v2": 0.5,
            }
        },
    }
    add_electrification(obj, kind, {"zone": info})

    sf = {"standard_heat_pump_v1": 0.2, "advanced_heat_pump_v2": 0.8}
    info = {"Maine": {"res_cooking": sf}}
    add_electrification(obj, kind, {"zone": info})

    result = obj.ct[kind]
    assert "Maine" in result["zone"]
    assert "New York City" in result["zone"]


def test_add_electrification_combined():
    obj = ChangeTable(Grid("Eastern"))
    kind = "building"
    sf = {"standard_heat_pump_v1": 0.2, "advanced_heat_pump_v2": 0.8}
    zone = {"Maine": {"res_cooking": sf}}
    grid = {"res_heating": sf}

    info = {"grid": grid, "zone": zone}
    add_electrification(obj, kind, info)

    assert info == obj.ct[kind]
