import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from powersimdata.design.generation.cost_curves import (
    KS_test,
    build_supply_curve,
    get_supply_data,
    lower_bound_index,
)
from powersimdata.input.grid import Grid
from powersimdata.tests.mock_grid import MockGrid

mock_plant = {
    "plant_id": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
    "type": [
        "coal",
        "coal",
        "ng",
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
    "Pmin": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
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
    "interconnect": [
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
        "D",
    ],
    "zone_name": [
        "A",
        "A",
        "A",
        "A",
        "B",
        "B",
        "B",
        "B",
        "B",
        "B",
        "C",
        "C",
        "C",
        "C",
        "C",
        "C",
        "C",
        "C",
        "C",
        "C",
    ],
}

mock_gencost = {
    "plant_id": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
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
}

grid_attrs = {"plant": mock_plant, "gencost_after": mock_gencost}

grid = MockGrid(grid_attrs)


def test_get_supply_data():
    supply_df = get_supply_data(grid)
    test_slope = supply_df["slope"]
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
        name="slope",
    )
    assert_series_equal(test_slope, exp_slope)


def test_build_supply_curve():
    supply_df = get_supply_data(grid)
    Ptest, Ftest = build_supply_curve(supply_df, "B", "ng", plot=False)
    Pexp = [0, 10, 10, 30, 30, 50, 50, 100, 100, 200]
    Fexp = [25.10, 25.10, 30.40, 30.40, 30.40, 30.40, 31.25, 31.25, 40.00, 40.00]
    assert all([Ptest[i] == Pexp[i] for i in range(len(Ptest))])
    assert all([Ftest[i] == Fexp[i] for i in range(len(Ptest))])


def test_KS_test():
    supply_df = get_supply_data(grid)
    P1, F1 = build_supply_curve(supply_df, "C", "coal", plot=False)
    P2 = [0, 15, 15, 40, 40, 75, 75, 130, 130, 190, 190, 225, 225, max(P1)]
    F2 = [
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
    test_diff = KS_test(P1, F1, P2, F2, plot=False)
    exp_diff = 4.5
    assert test_diff == exp_diff


def test_lower_bound_index():
    x = 10
    l = [0, 5, 5, 9, 9, 12, 12, 18]
    ind_test = lower_bound_index(x, l)
    ind_exp = 4
    assert ind_test == ind_exp
