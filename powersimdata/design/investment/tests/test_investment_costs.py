import pytest

from powersimdata.design.investment.inflation import calculate_inflation
from powersimdata.design.investment.investment_costs import (
    _calculate_ac_inv_costs,
    _calculate_dc_inv_costs,
    _calculate_gen_inv_costs,
)
from powersimdata.tests.mock_grid import MockGrid

# bus_id is the index
mock_bus = {
    "bus_id": [2010228, 2021106, 2010319, 2010320],
    "lat": [47.6146, 37.7849, 47.6408, 47.6408],
    "lon": [-122.326, -122.407, -122.339, -122.339],
    "baseKV": [100, 346, 230, 800],
}

# branch 10-12 from Seattle (s3, p1, NWPP Coal) to San Francisco (s25, p9, NP15) (~679 miles)
# branch 13-14 are transformers (0 miles)
mock_branch = {
    "branch_id": [10, 11, 12, 13, 14],
    "rateA": [0, 10, 1100, 30, 40],
    "from_bus_id": [2010228, 2010228, 2010319, 2010319, 2021106],
    "to_bus_id": [2021106, 2021106, 2021106, 2010320, 2021106],
    "branch_device_type": 3 * ["Line"] + 2 * ["Transformer"],
}
mock_branch["from_lat"] = [
    mock_bus["lat"][mock_bus["bus_id"].index(bus)] for bus in mock_branch["from_bus_id"]
]
mock_branch["from_lon"] = [
    mock_bus["lon"][mock_bus["bus_id"].index(bus)] for bus in mock_branch["from_bus_id"]
]
mock_branch["to_lat"] = [
    mock_bus["lat"][mock_bus["bus_id"].index(bus)] for bus in mock_branch["to_bus_id"]
]
mock_branch["to_lon"] = [
    mock_bus["lon"][mock_bus["bus_id"].index(bus)] for bus in mock_branch["to_bus_id"]
]

mock_plant = {
    "plant_id": [3, 5, 6, 7, 8, 9, 10, 11],
    "bus_id": [2010228, 2010228, 2021106, 2010319, 2010319, 2010319, 2010320, 2021106],
    "type": ["solar", "coal", "wind", "solar", "solar", "ng", "wind", "nuclear"],
    "Pmax": [15, 30, 10, 12, 8, 20, 15, 1000],
}
mock_plant["lat"] = [
    mock_bus["lat"][mock_bus["bus_id"].index(bus)] for bus in mock_plant["bus_id"]
]
mock_plant["lon"] = [
    mock_bus["lon"][mock_bus["bus_id"].index(bus)] for bus in mock_plant["bus_id"]
]

mock_dcline = {
    "dcline_id": [5],
    "Pmax": [10],
    "from_bus_id": [2010228],
    "to_bus_id": [2021106],
}

mock_storage_gen = {
    "Pmax": [100, 200],
    "bus_id": [2010228, 2021106],
    "type": ["storage"] * 2,
}
mock_storage_data = {"UnitIdx": [12, 13]}

grid_attrs = {
    "plant": mock_plant,
    "bus": mock_bus,
    "branch": mock_branch,
    "dcline": mock_dcline,
    "storage_gen": mock_storage_gen,
    "storage_StorageData": mock_storage_data,
}


@pytest.fixture
def mock_grid():
    return MockGrid(grid_attrs)


def test_calculate_ac_inv_costs(mock_grid):
    expected_ac_cost = {
        # ((reg_mult1 + reg_mult2) / 2) * sum(basecost * rateA * miles)
        "line_cost": (
            ((1 + 2.25) / 2)
            * (3666.67 * 10 * 679.179925842 + 1500 * 1100 * 680.986501516)
            * calculate_inflation(2010)
        ),
        # for each: rateA * basecost * regional multiplier
        "transformer_cost": ((30 * 7670 * 1) + (40 * 8880 * 2.25))
        * calculate_inflation(2020),
    }
    ac_cost = _calculate_ac_inv_costs(mock_grid)
    assert ac_cost.keys() == expected_ac_cost.keys()
    for k in ac_cost.keys():
        assert ac_cost[k] == pytest.approx(expected_ac_cost[k])


def test_calculate_ac_inv_costs_not_summed(mock_grid):
    inflation_2010 = calculate_inflation(2010)
    inflation_2020 = calculate_inflation(2020)
    expected_ac_cost = {
        # ((reg_mult1 + reg_mult2) / 2) * sum(basecost * rateA * miles)
        "line_cost": {
            10: 0,  # This branch would normally be dropped by calculate_ac_inv_costs
            11: ((1 + 2.25) / 2) * 3666.67 * 10 * 679.179925842 * inflation_2010,
            12: ((1 + 2.25) / 2) * 1500 * 1100 * 680.986501516 * inflation_2010,
        },
        # for each: rateA * basecost * regional multiplier
        "transformer_cost": {
            13: (30 * 7670 * 1) * inflation_2020,
            14: (40 * 8880 * 2.25) * inflation_2020,
        },
    }
    ac_cost = _calculate_ac_inv_costs(mock_grid, sum_results=False)
    for branch_type, upgrade_costs in expected_ac_cost.items():
        assert set(upgrade_costs.keys()) == set(ac_cost[branch_type].index)
        for branch, cost in upgrade_costs.items():
            assert cost == pytest.approx(ac_cost[branch_type].loc[branch, "Cost"])


def test_calculate_dc_inv_costs(mock_grid):
    expected_dc_cost = (
        # lines
        10 * 679.1799258421203 * 457.1428571 * calculate_inflation(2015)
        # terminals
        + 135e3 * 10 * 2 * calculate_inflation(2020)
    )
    dc_cost = _calculate_dc_inv_costs(mock_grid)
    assert dc_cost == pytest.approx(expected_dc_cost)


def test_calculate_gen_inv_costs_2030(mock_grid):
    gen_inv_cost = _calculate_gen_inv_costs(mock_grid, 2030, "Moderate").to_dict()
    expected_gen_inv_cost = {
        # for each: capacity (kW) * regional multiplier * base technology cost
        "solar": sum(
            [
                15e3 * 1.01701 * 836.3842785,
                12e3 * 1.01701 * 836.3842785,
                8e3 * 1.01701 * 836.3842785,
            ]
        ),
        "coal": 30e3 * 1.05221 * 4049.047403,
        "wind": 10e3 * 1.16979 * 1297.964758 + 15e3 * 1.04348 * 1297.964758,
        "ng": 20e3 * 1.050755 * 983.2351768,
        "storage": 100e3 * 1.012360 * 817 + 200e3 * 1.043730 * 817,
        "nuclear": 1000e3 * 1.07252 * 6727.799801,
    }
    inflation = calculate_inflation(2018)
    expected_gen_inv_cost = {k: v * inflation for k, v in expected_gen_inv_cost.items()}
    assert gen_inv_cost.keys() == expected_gen_inv_cost.keys()
    for k in gen_inv_cost.keys():
        assert gen_inv_cost[k] == pytest.approx(expected_gen_inv_cost[k])


def test_calculate_gen_inv_costs_not_summed(mock_grid):
    gen_inv_cost = _calculate_gen_inv_costs(
        mock_grid, 2025, "Advanced", sum_results=False
    )
    expected_gen_inv_cost = {
        # for each: capacity (kW) * regional multiplier * base technology cost
        3: 15e3 * 1.01701 * 1013.912846,
        5: 30e3 * 1.05221 * 4099.115851,
        6: 10e3 * 1.16979 * 1301.120135,
        7: 12e3 * 1.01701 * 1013.912846,
        8: 8e3 * 1.01701 * 1013.912846,
        9: 20e3 * 1.050755 * 1008.001936,
        10: 15e3 * 1.04348 * 1301.120135,
        11: 1000e3 * 1.07252 * 6928.866991,
        12: 100e3 * 1.012360 * 779,
        13: 200e3 * 1.043730 * 779,
    }
    inflation = calculate_inflation(2018)
    expected_gen_inv_cost = {k: v * inflation for k, v in expected_gen_inv_cost.items()}
    assert set(gen_inv_cost.index) == set(expected_gen_inv_cost.keys())
    for k in gen_inv_cost.index:
        assert gen_inv_cost.loc[k, "CAPEX_total"] == pytest.approx(
            expected_gen_inv_cost[k]
        )
