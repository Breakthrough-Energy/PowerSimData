import pytest

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
    "from_bus_id": [2010228, 2010228, 2010319, 2010319, 2010320],
    "to_bus_id": [2021106, 2021106, 2021106, 2010320, 2010319],
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
    "plant_id": ["A", "B", "C", "D", "E", "F", "G"],
    "bus_id": [2010228, 2010228, 2021106, 2010319, 2010319, 2010319, 2010320],
    "type": ["solar", "coal", "wind", "solar", "solar", "ng", "wind"],
    "Pmax": [15, 30, 10, 12, 8, 20, 15],
}

mock_dcline = {
    "dcline_id": [5],
    "Pmax": [10],
    "from_bus_id": [2010228],
    "to_bus_id": [2021106],
}

grid_attrs = {
    "plant": mock_plant,
    "bus": mock_bus,
    "branch": mock_branch,
    "dcline": mock_dcline,
}

@pytest.fixture
def mock_grid():
    return MockGrid(grid_attrs)


def test_calculate_ac_inv_costs(mock_grid):
    expected_ac_cost = {
        # ((reg_mult1 + reg_mult2) / 2) * sum(basecost * rateA * miles)
        "line_cost": ((1 + 2.25) / 2)
        * (3666.67 * 10 * 679.179925842 + 1500 * 1100 * 680.986501516),
        "transformer_cost": 5500000 + 42500000,
    }
    ac_cost = _calculate_ac_inv_costs(mock_grid, "2025")
    assert ac_cost.keys() == expected_ac_cost.keys()
    for k in ac_cost.keys():
        assert ac_cost[k] == pytest.approx(expected_ac_cost[k])


def test_calculate_dc_inv_costs(mock_grid):
    expected_dc_cost = 10 * 679.1799258421203 * 457.1428571 + 550000000
    dc_cost = _calculate_dc_inv_costs(mock_grid, "2025")
    assert dc_cost == pytest.approx(expected_dc_cost)
