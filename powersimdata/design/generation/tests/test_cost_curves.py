import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

from powersimdata.design.generation.cost_curves import (
    build_supply_curve,
    get_supply_data,
    ks_test,
    linearize_gencost,
    lower_bound_index,
)
from powersimdata.tests.mock_grid import MockGrid

mock_plant = {
    "plant_id": range(20),
    "type": [
        "coal",
        "coal",
        "coal",
        "ng",
        "coal",
        "ng",
        "ng",
        "ng",
        "ng",
        "ng",
        "coal",
        "coal",
        "coal",
        "coal",
        "coal",
        "coal",
        "coal",
        "ng",
        "ng",
        "ng",
    ],
    "Pmin": [0] * 20,
    "Pmax": [
        50,
        20,
        100,
        10,
        10,
        10,
        100,
        20,
        20,
        50,
        100,
        10,
        10,
        10,
        20,
        50,
        50,
        20,
        20,
        100,
    ],
    "interconnect": ["Western"] * 20,
    "zone_name": ["Utah"] * 4 + ["Colorado"] * 6 + ["Washington"] * 10,
}

mock_gencost = {
    "plant_id": range(20),
    "type": [2] * 20,
    "startup": [0] * 20,
    "shutdown": [0] * 20,
    "n": [3] * 20,
    "c2": [
        0.025,
        0.010,
        0.050,
        0.010,
        0.020,
        0.010,
        0.050,
        0.020,
        0.020,
        0.025,
        0.025,
        0.020,
        0.010,
        0.010,
        0.020,
        0.020,
        0.025,
        0.020,
        0.010,
        0.050,
    ],
    "c1": [
        30,
        30,
        35,
        30,
        25,
        25,
        35,
        30,
        30,
        30,
        35,
        25,
        25,
        30,
        30,
        30,
        30,
        25,
        25,
        35,
    ],
    "c0": [
        1300,
        1100,
        1700,
        1100,
        1000,
        1200,
        1900,
        1200,
        1100,
        1400,
        1800,
        1100,
        1100,
        1200,
        1400,
        1500,
        1300,
        1100,
        1200,
        1900,
    ],
    "interconnect": ["Western"] * 20,
}

grid_attrs = {"plant": mock_plant, "gencost_before": mock_gencost}

grid = MockGrid(grid_attrs)
grid.interconnect = "Western"
grid.zone2id = {"Utah": 210, "Colorado": 212, "Washington": 201}

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


def test_linearize_gencost():
    actual = linearize_gencost(mock_grid_gc)
    assert_frame_equal(expected_one_segment, actual, check_dtype=False)


def test_linearize_gencost_two_segment():
    actual = linearize_gencost(mock_grid_gc, num_segments=2)
    assert_frame_equal(expected_two_segment, actual, check_dtype=False)


def test_linearize_gencost_pmin_equal_pmax():
    plant = mock_grid_gc.plant.copy()
    plant.Pmin = plant.Pmax
    grid = MockGrid({"plant": plant.reset_index().to_dict(), "gencost_before": mock_gc})
    actual = linearize_gencost(grid, num_segments=3)
    assert_frame_equal(expected_all_equal, actual, check_dtype=False)


def test_get_supply_data():
    supply_df = get_supply_data(grid, 1)
    test_slope = supply_df["slope1"]
    exp_slope = pd.Series(
        [
            31.25,
            30.20,
            40.00,
            30.10,
            25.20,
            25.10,
            40.00,
            30.40,
            30.40,
            31.25,
            37.50,
            25.20,
            25.10,
            30.10,
            30.40,
            31.00,
            31.25,
            25.40,
            25.20,
            40.00,
        ],
        index=supply_df.index,
        name="slope1",
    )
    assert_series_equal(test_slope, exp_slope)


def test_build_supply_curve_1seg():
    capacity_test, price_test = build_supply_curve(
        grid, 1, "Colorado", "ng", "loadzone", plot=False
    )
    capacity_exp = [0, 10, 10, 30, 30, 50, 50, 100, 100, 200]
    price_exp = [
        25.10,
        25.10,
        30.40,
        30.40,
        30.40,
        30.40,
        31.25,
        31.25,
        40.00,
        40.00,
    ]
    assert all([capacity_test[i] == capacity_exp[i] for i in range(len(capacity_test))])
    assert all([price_test[i] == price_exp[i] for i in range(len(capacity_test))])


def test_build_supply_curve_2seg():
    capacity_test, price_test = build_supply_curve(
        grid, 2, "Utah", "coal", "loadzone", plot=False
    )
    capacity_exp = [0, 10, 10, 20, 20, 45, 45, 70, 70, 120, 120, 170]
    price_exp = [
        30.100,
        30.100,
        30.300,
        30.300,
        30.625,
        30.625,
        31.875,
        31.875,
        37.500,
        37.500,
        42.500,
        42.500,
    ]
    assert all([capacity_test[i] == capacity_exp[i] for i in range(len(capacity_test))])
    assert all([price_test[i] == price_exp[i] for i in range(len(capacity_test))])


def test_ks_test():
    capacity_data1, price_data1 = build_supply_curve(
        grid, 1, "Washington", "coal", "loadzone", plot=False
    )
    capacity_data2 = [
        0,
        15,
        15,
        40,
        40,
        75,
        75,
        130,
        130,
        190,
        190,
        225,
        225,
        max(capacity_data1),
    ]
    price_data2 = [
        23.00,
        23.00,
        27.00,
        27.00,
        29.00,
        29.00,
        30.00,
        30.00,
        33.00,
        33.00,
        34.00,
        34.00,
        38.00,
        38.00,
    ]
    test_diff = ks_test(
        capacity_data1, price_data1, capacity_data2, price_data2, plot=False
    )
    exp_diff = 4.5
    assert test_diff == exp_diff


def test_lower_bound_index():
    desired_capacity = 10
    capacity_data = [0, 5, 5, 9, 9, 12, 12, 18]
    ind_test = lower_bound_index(desired_capacity, capacity_data)
    ind_exp = 4
    assert ind_test == ind_exp
