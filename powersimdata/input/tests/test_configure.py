import pandas as pd
from pandas.testing import assert_frame_equal

from powersimdata.input.configure import linearize_gencost
from powersimdata.tests.mock_grid import MockGrid

mock_gc = {
    "plant_id": range(3),
    "type": [2, 2, 2],
    "startup": [0, 0, 0],
    "shutdown": [0, 0, 0],
    "n": [3, 3, 3],
    "c2": [1, 2, 3],
    "c1": [4, 5, 6],
    "c0": [7, 8, 9],
    "interconnect": ["Western"] * 3,
}
mock_plant_gc = {"plant_id": range(3), "Pmin": [20, 40, 60], "Pmax": [50, 100, 150]}
grid_attrs_gc = {
    "plant": mock_plant_gc,
    "gencost_before": mock_gc,
}
mock_grid_gc = MockGrid(grid_attrs_gc)

expected_one_segment = pd.DataFrame(
    {
        "plant_id": range(3),
        "type": [1, 1, 1],
        "startup": [0, 0, 0],
        "shutdown": [0, 0, 0],
        "n": [2, 2, 2],
        "c2": [1, 2, 3],
        "c1": [4, 5, 6],
        "c0": [7, 8, 9],
        "p1": [20, 40, 60],
        "f1": [
            (1 * 20**2 + 4 * 20 + 7),
            (2 * 40**2 + 5 * 40 + 8),
            (3 * 60**2 + 6 * 60 + 9),
        ],
        "p2": [50, 100, 150],
        "f2": [
            (1 * 50**2 + 4 * 50 + 7),
            (2 * 100**2 + 5 * 100 + 8),
            (3 * 150**2 + 6 * 150 + 9),
        ],
        "interconnect": ["Western"] * 3,
    }
).set_index("plant_id")

expected_two_segment = expected_one_segment.copy()
expected_two_segment.n = 3
expected_two_segment["p3"] = expected_one_segment["p2"].copy()
expected_two_segment["f3"] = expected_one_segment["f2"].copy()
expected_two_segment.p2 = [35, 70, 105]
expected_two_segment.f2 = [
    1 * 35**2 + 4 * 35 + 7,
    2 * 70**2 + 5 * 70 + 8,
    3 * 105**2 + 6 * 105 + 9,
]
expected_two_segment["interconnect"] = expected_two_segment.pop("interconnect")

expected_all_equal = mock_grid_gc.gencost["before"].copy()
expected_all_equal.c2 = 0
expected_all_equal.c1 = 0
expected_all_equal.c0 = [2707, 20508, 68409]


def _linearize_gencost(grid, num_segments=1):
    before = grid.gencost["before"]
    return linearize_gencost(before, grid.plant, num_segments)


def test_linearize_gencost():
    actual = _linearize_gencost(mock_grid_gc)
    assert_frame_equal(expected_one_segment, actual, check_dtype=False)


def test_linearize_gencost_two_segment():
    actual = _linearize_gencost(mock_grid_gc, num_segments=2)
    assert_frame_equal(expected_two_segment, actual, check_dtype=False)


def test_linearize_gencost_pmin_equal_pmax():
    plant = mock_grid_gc.plant.copy()
    plant.Pmin = plant.Pmax
    grid = MockGrid({"plant": plant.reset_index().to_dict(), "gencost_before": mock_gc})
    actual = _linearize_gencost(grid, num_segments=3)
    assert_frame_equal(expected_all_equal, actual, check_dtype=False)
