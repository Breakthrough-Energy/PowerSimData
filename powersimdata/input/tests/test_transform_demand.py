import pandas as pd

from powersimdata.input.change_table import ChangeTable
from powersimdata.input.grid import Grid
from powersimdata.input.transform_demand import TransformDemand
from powersimdata.tests.mock_profile_input import MockProfileInput


def test_profile_mappings():
    grid = Grid("Texas")
    ct = ChangeTable(grid)
    grid_info = {"res_heating": {"standard_heat_pump_v2": 0.3}}
    zone_info = {
        "East": {"res_cooking": {"advanced_heat_pump_v2": 0.7}},
        "Coast": {
            "com_hot_water": {
                "standard_heat_pump_v1": 0.6,
                "advanced_heat_pump_v2": 0.4,
            }
        },
        "Far West": {
            "res_cooking": {"standard_heat_pump_v1": 0.2, "advanced_heat_pump_v2": 0.3}
        },
    }

    kind = "building"
    ct.add_electrification(kind, {"zone": zone_info, "grid": grid_info})
    td = TransformDemand(grid, ct, kind)

    actual = td.p2g
    expected = {"res_heating_standard_heat_pump_v2.csv": 0.3}
    assert expected == actual

    actual = td.p2z
    expected = {
        "res_cooking_advanced_heat_pump_v2.csv": [(308, 0.7), (301, 0.3)],
        "com_hot_water_standard_heat_pump_v1.csv": [(307, 0.6)],
        "com_hot_water_advanced_heat_pump_v2.csv": [(307, 0.4)],
        "res_cooking_standard_heat_pump_v1.csv": [(301, 0.2)],
    }

    assert expected == actual


def test_aggregate_demand():
    grid = Grid("Texas")
    ct = ChangeTable(grid)
    kind = "building"
    zone_info = {"East": {"res_cooking": {"advanced_heat_pump_v2": 0.7}}}
    grid_info = {"res_cooking": {"advanced_heat_pump_v2": 0.3}}
    ct.add_electrification(kind, {"zone": zone_info, "grid": grid_info})

    mock_input = MockProfileInput(grid)
    demand = mock_input.get_data(None, "demand")
    mock_input.get_profile = lambda *args: demand

    td = TransformDemand(grid, ct, kind)
    td._profile_data = mock_input
    result = td.value()

    pd.testing.assert_series_equal(0.7 * demand.loc[:, 308], result.loc[:, 308])
    pd.testing.assert_frame_equal(0.3 * demand.loc[:, :307], result.loc[:, :307])
