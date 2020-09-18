import pytest
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

from powersimdata.input.grid import Grid
from powersimdata.design.generation.cost_curves import (
    get_supply_data,
    build_supply_curve,
    lower_bound_index,
    KS_test,
    plot_c1_vs_c2,
    plot_capacity_vs_price,
)
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
        0.01,
        0.05,
        0.01,
        0.02,
        0.01,
        0.05,
        0.02,
        0.02,
        0.025,
        0.025,
        0.02,
        0.01,
        0.01,
        0.02,
        0.02,
        0.025,
        0.02,
        0.01,
        0.05,
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
supply_df = get_supply_data(grid)


def test_build_supply_curve():
    Ptest, Ftest = build_supply_curve(supply_df, "B", "ng", plot=False)
    Pexp = [0, 10, 10, 30, 30, 50, 50, 100, 100, 200]
    Fexp = [25.1, 25.1, 30.4, 30.4, 30.4, 30.4, 31.25, 31.25, 40.0, 40.0]
    assert all([Ptest[i] == Pexp[i] for i in range(len(Ptest))])
    assert all([Ftest[i] == Fexp[i] for i in range(len(Ptest))])


def test_KS_test():
    P1, F1 = build_supply_curve(supply_df, "C", "coal", plot=False)
    P2 = [0, 15, 15, 40, 40, 75, 75, 130, 130, 190, 190, 225, 225, max(P1)]
    F2 = [
        23.0,
        23.0,
        27.0,
        27.0,
        29.0,
        29.0,
        30.0,
        30.0,
        33.0,
        33.0,
        34.0,
        34.0,
        38.0,
        38.0,
    ]
    test_diff = KS_test(P1, F1, P2, F2, plot=False)
    exp_diff = 4.5
    assert test_diff == exp_diff


def test_lower_bound_index():
    x = 10
    l = [0, 5, 5, 9, 9, 12, 12, 18]
    itest = lower_bound_index(x, l)
    iexp = 4
    assert itest == iexp
