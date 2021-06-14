import pandas as pd

from powersimdata.design.transmission.substations import calculate_substation_capacity
from powersimdata.tests.mock_grid import MockGrid


def test_calculate_substation_capacity():
    mock_sub = {"sub_id": [1, 2, 3, 4]}
    mock_bus2sub = {"bus_id": [10, 20, 21, 30, 40], "sub_id": [1, 2, 2, 3, 4]}
    mock_branch = {
        "branch_id": [200, 400, 420, 600, 601, 1200],
        "from_bus_id": [10, 40, 20, 20, 30, 30],
        "to_bus_id": [20, 10, 21, 30, 20, 40],
        "rateA": [1, 2, 4, 8, 16, 32],
    }

    mock_grid_data = {
        "sub": mock_sub,
        "bus2sub": mock_bus2sub,
        "branch": mock_branch,
    }
    mock_grid = MockGrid(grid_attrs=mock_grid_data)
    substation_capacity = calculate_substation_capacity(mock_grid)
    expected_return = pd.Series(
        {
            1: 3,
            2: 25,
            3: 56,
            4: 34,
        }
    )
    assert substation_capacity.equals(expected_return)
