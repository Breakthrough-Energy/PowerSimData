import pytest

from powersimdata.input.change_table import ChangeTable
from powersimdata.input.changes.electrification import add_electrification
from powersimdata.input.grid import Grid


def test_add_electrification():
    obj = ChangeTable(Grid("Texas"))
    kind = "building"

    info = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": 0.3}
    add_electrification(obj, kind, info)

    with pytest.raises(ValueError):
        add_electrification(obj, "foo", info)

    with pytest.raises(ValueError):
        info = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": -3}
        add_electrification(obj, kind, info)

    with pytest.raises(ValueError):
        info = {"standard_heat_pump_v1": 0.7, "advanced_heat_pump_v2": 0.8}
        add_electrification(obj, kind, info)


def test_add_electrification_by_zone():
    obj = ChangeTable(Grid("Eastern"))
    kind = "building"

    info = {
        "New York City": {"standard_heat_pump_v1": 0.3, "advanced_heat_pump_v2": 0.7},
        "Western North Carolina": {
            "standard_heat_pump_v1": 0.5,
            "advanced_heat_pump_v2": 0.5,
        },
        "Maine": {"standard_heat_pump_v1": 0.2, "advanced_heat_pump_v2": 0.8},
    }
    add_electrification(obj, kind, info)

    with pytest.raises(ValueError):
        info = {1: {"foo": 3}, "wrong": {}}
        add_electrification(obj, kind, info)
