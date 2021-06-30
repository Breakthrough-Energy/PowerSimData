import datetime

import numpy as np
import pandas as pd
import pytest

from powersimdata import Grid
from powersimdata.input.check import (
    _check_areas_and_format,
    _check_areas_are_in_grid_and_format,
    _check_data_frame,
    _check_date,
    _check_date_range_in_scenario,
    _check_date_range_in_time_series,
    _check_epsilon,
    _check_gencost,
    _check_grid_models_match,
    _check_grid_type,
    _check_number_hours_to_analyze,
    _check_plants_are_in_grid,
    _check_resources_and_format,
    _check_resources_are_in_grid_and_format,
    _check_resources_are_renewable_and_format,
    _check_time_series,
    check_grid,
)
from powersimdata.tests.mock_scenario import MockScenario


@pytest.fixture
def mock_plant():
    return {
        "plant_id": range(15),
        "type": [
            "solar",
            "nuclear",
            "wind",
            "wind_offshore",
            "coal",
            "ng",
            "coal",
            "coal",
            "geothermal",
            "wind",
            "solar",
            "hydro",
            "coal",
            "ng",
            "solar",
        ],
        "interconnect": ["Western"] * 3 + ["Texas"] * 8 + ["Eastern"] * 4,
        "zone_name": [
            "Washington",
            "El Paso",
            "Bay Area",
        ]
        + [
            "Far West",
            "North",
            "West",
            "South",
            "North Central",
            "South Central",
            "Coast",
            "East",
        ]
        + ["Kentucky", "Nebraska", "East Texas", "Texas Panhandle"],
    }


@pytest.fixture
def mock_gencost():
    return {
        "plant_id": range(15),
        "type": [2] * 15,
        "startup": [0] * 15,
        "shutdown": [0] * 15,
        "n": [3] * 15,
        "c2": [
            0,
            0.00021,
            0,
            0,
            0.00125,
            0.0015,
            0.00085,
            0.0009,
            0,
            0,
            0,
            0,
            0.0013,
            0.0011,
            0,
        ],
        "c1": [0, 20, 0, 0, 25, 32, 18, 29, 0, 0, 0, 0, 35, 27, 0],
        "c0": [0, 888, 0, 0, 750, 633, 599, 933, 0, 0, 0, 0, 1247, 1111, 0],
        "interconnect": ["Western"] * 15,
    }


@pytest.fixture
def mock_scenario(mock_plant, mock_gencost):
    mock_scenario = MockScenario({"plant": mock_plant, "gencost_after": mock_gencost})
    mock_scenario.info["start_date"] = "2016-01-01 00:00:00"
    mock_scenario.info["end_date"] = "2016-01-10 23:00:00"
    return mock_scenario


@pytest.fixture
def mock_grid(mock_scenario):
    return mock_scenario.get_grid()


def test_error_handling():
    grid = Grid("Western")
    del grid.dcline
    with pytest.raises(ValueError):
        check_grid(grid)


@pytest.mark.parametrize(
    "interconnect", ["Eastern", "Western", "Texas", ["Western", "Texas"], "USA"]
)
def test_check_grid(interconnect):
    grid = Grid(interconnect)
    check_grid(grid)


def check_grid_models_match_success():
    _check_grid_models_match(Grid("Western"), Grid("Texas"))


def check_grid_models_match_failure():
    grid1 = Grid("Western")
    grid2 = Grid("Texas")
    grid2.grid_model == "foo"
    with pytest.raises(ValueError):
        _check_grid_models_match(grid1, grid2)


def test_check_data_frame_argument_type():
    arg = (
        (1, "int"),
        ("homer", "str"),
        ({"homer", "marge", "bart", "lida"}, "set"),
        (pd.DataFrame({"California": [1, 2, 3], "Texas": [4, 5, 6]}), 123456),
    )
    for a in arg:
        with pytest.raises(TypeError):
            _check_data_frame(a[0], a[1])


def test_check_data_frame_argument_value():
    arg = (
        (pd.DataFrame({"California": [], "Texas": []}), "row"),
        (pd.DataFrame({}), "col"),
    )
    for a in arg:
        with pytest.raises(ValueError):
            _check_data_frame(a[0], a[1])


def test_check_data_frame():
    _check_data_frame(
        pd.DataFrame({"California": [1, 2, 3], "Texas": [4, 5, 6]}), "pandas.DataFrame"
    )


def test_check_time_series_argument_value():
    ts = pd.DataFrame({"demand": [200, 100, 10, 75, 150]})
    with pytest.raises(ValueError):
        _check_time_series(ts, "demand")


def test_check_time_series():
    ts = pd.DataFrame(
        {"demand": [200, 100, 10, 75, 150]},
        index=pd.date_range("2018-01-01", periods=5, freq="H"),
    )
    _check_time_series(ts, "demand")

    ts = pd.Series(
        [200, 100, 10, 75, 150],
        index=pd.date_range("2018-01-01", periods=5, freq="H"),
    )
    _check_time_series(ts, "demand")


def test_check_grid_type_failure():
    arg = (1, pd.DataFrame({"California": [1, 2, 3], "Texas": [4, 5, 6]}))
    for a in arg:
        with pytest.raises(TypeError):
            _check_grid_type(a)


def test_check_grid_type_success(mock_grid):
    _check_grid_type(mock_grid)


def test_check_areas_and_format_argument_type():
    arg = (
        1,
        {"California": [1, 2, 3], "Texas": [4, 5, 6]},
        [1, 2, 3, 4],
        (1, 2, 3, 4),
        ("a", "b", "c", 4),
    )
    for a in arg:
        with pytest.raises(TypeError):
            _check_areas_and_format()


def test_check_areas_and_format_argument_value():
    arg = ([], {"Texas", "Louisane", "Florida", "Canada"}, {"France"})
    for a in arg:
        with pytest.raises(ValueError):
            _check_areas_and_format(a)


def test_check_areas_and_format():
    _check_areas_and_format(["Western", "NY", "El Paso", "Arizona"])
    areas = _check_areas_and_format(["California", "CA", "NY", "TX", "MT", "WA"])
    assert areas == {"Washington", "Texas", "Montana", "California", "New York"}


def test_check_resources_and_format_argument_type():
    arg = (
        1,
        {"coal": [1, 2, 3], "htdro": [4, 5, 6]},
        [1, 2, 3, 4],
        (1, 2, 3, 4),
        {1, 2, 3, 4},
        ("a", "b", "c", 4),
    )
    for a in arg:
        with pytest.raises(TypeError):
            _check_resources_and_format(a)


def test_check_resources_and_format_argument_value():
    arg = ((), {"solar", "nuclear", "ng", "battery"}, {"geo-thermal"})
    for a in arg:
        with pytest.raises(ValueError):
            _check_resources_and_format(a)


def test_check_resources_and_format():
    _check_resources_and_format(["dfo", "wind", "solar", "ng"])
    _check_resources_and_format("wind_offshore")
    _check_resources_and_format({"nuclear"})


def test_check_resources_are_renewable_and_format_argument_value():
    with pytest.raises(ValueError):
        _check_resources_are_renewable_and_format({"solar", "nuclear"})


def test_check_resources_are_renewable_and_format():
    _check_resources_are_renewable_and_format(["wind_offshore", "wind"])
    _check_resources_are_renewable_and_format("solar")
    _check_resources_are_renewable_and_format({"wind"})


def test_check_areas_are_in_grid_and_format_argument_type(mock_grid):
    arg = (({"Texas", "El Paso"}, mock_grid), ({123: "Nebraska"}, mock_grid))
    for a in arg:
        with pytest.raises(TypeError):
            _check_areas_are_in_grid_and_format(a[0], a[1])


def test_check_areas_are_in_grid_and_format_argument_value(mock_grid):
    arg = (
        ({"county": "Kentucky"}, mock_grid),
        ({"state": "California"}, mock_grid),
        ({"loadzone": "Texas"}, mock_grid),
        ({"state": "El Paso"}, mock_grid),
        ({"interconnect": "Nebraska"}, mock_grid),
    )
    for a in arg:
        with pytest.raises(ValueError):
            _check_areas_are_in_grid_and_format(a[0], a[1])


def test_check_areas_are_in_grid_and_format(mock_grid):
    assert _check_areas_are_in_grid_and_format(
        {
            "state": {"Washington", "Kentucky", "NE", "TX", "WA"},
            "loadzone": ["Washington", "East", "El Paso", "Bay Area"],
            "interconnect": "Texas",
        },
        mock_grid,
    ) == {
        "interconnect": {"Texas"},
        "state": {"Washington", "Kentucky", "Nebraska", "Texas"},
        "loadzone": {"Washington", "East", "El Paso", "Bay Area"},
    }


def test_check_resources_are_in_grid_and_format_argument_value(mock_grid):
    arg = (({"solar", "dfo"}, mock_grid), ({"uranium"}, mock_grid))
    for a in arg:
        with pytest.raises(ValueError):
            _check_resources_are_in_grid_and_format(a[0], a[1])


def test_check_resources_are_in_grid_and_format(mock_grid):
    _check_resources_are_in_grid_and_format({"solar", "coal", "hydro"}, mock_grid)
    _check_resources_are_in_grid_and_format(
        ["solar", "ng", "hydro", "nuclear"], mock_grid
    )


def test_check_plants_are_in_grid_argument_type(mock_grid):
    arg = (
        (str(mock_grid.plant.index[1]), mock_grid),
        (mock_grid.plant.index[:3], mock_grid),
        (mock_grid.plant.index[0], mock_grid.plant),
    )
    for a in arg:
        with pytest.raises(TypeError):
            _check_plants_are_in_grid(a[0], a[1])


def test_check_plants_are_in_grid_argument_value(mock_grid):
    with pytest.raises(ValueError):
        _check_plants_are_in_grid(
            [p + 100 for p in mock_grid.plant.index[-5:]], mock_grid
        )


def test_check_plants_are_in_grid(mock_grid):
    _check_plants_are_in_grid([p for p in mock_grid.plant.index[:5]], mock_grid)
    _check_plants_are_in_grid([str(p) for p in mock_grid.plant.index[:5]], mock_grid)
    _check_plants_are_in_grid(set([p for p in mock_grid.plant.index[:5]]), mock_grid)
    _check_plants_are_in_grid(tuple([p for p in mock_grid.plant.index[:5]]), mock_grid)


def test_check_number_hours_to_analyze_argument_type(mock_scenario):
    arg = ((mock_scenario, "100"), (mock_scenario, [100]), (mock_scenario, {100, 50}))
    for a in arg:
        with pytest.raises(TypeError):
            _check_number_hours_to_analyze(a[0], a[1])


def test_check_number_hours_to_analyze_argument_value(mock_scenario):
    arg = ((mock_scenario, -10), (mock_scenario, 15 * 24))
    for a in arg:
        with pytest.raises(ValueError):
            _check_number_hours_to_analyze(a[0], a[1])


def test_check_number_hours_to_analyze(mock_scenario):
    _check_number_hours_to_analyze(mock_scenario, 24)


def test_check_date_argument_type():
    with pytest.raises(TypeError):
        _check_date("2016-02-01 00:00:00")


def test_check_date():
    _check_date(datetime.datetime(2020, 9, 9))
    _check_date(np.datetime64("1981-06-21"))
    _check_date(pd.Timestamp(2016, 2, 1))


def test_check_date_range_in_scenario_argument_value(mock_scenario):
    arg = (
        (mock_scenario, pd.Timestamp(2016, 1, 5), pd.Timestamp(2016, 1, 2)),
        (mock_scenario, pd.Timestamp(2015, 12, 1), pd.Timestamp(2016, 1, 8)),
        (mock_scenario, pd.Timestamp(2016, 1, 2), pd.Timestamp(2016, 2, 15)),
    )
    for a in arg:
        with pytest.raises(ValueError):
            _check_date_range_in_scenario(a[0], a[1], a[2])


def test_check_date_range_in_scenario(mock_scenario):
    _check_date_range_in_scenario(
        mock_scenario, pd.Timestamp(2016, 1, 2), pd.Timestamp(2016, 1, 7)
    )


def test_check_date_range_in_time_series_argument_value():
    data = {
        "A": np.random.randint(0, high=1000, size=366 * 24),
        "B": np.random.randn(366 * 24),
    }

    ts = pd.DataFrame(
        data, index=pd.date_range("2016-01-01", periods=366 * 24, freq="H")
    )

    arg = (
        (ts, pd.Timestamp(2016, 5, 5), pd.Timestamp(2016, 3, 28)),
        (ts, pd.Timestamp(2015, 12, 1), pd.Timestamp(2016, 8, 8)),
        (ts, pd.Timestamp(2016, 3, 2), pd.Timestamp(2017, 2, 15)),
    )
    for a in arg:
        with pytest.raises(ValueError):
            _check_date_range_in_time_series(a[0], a[1], a[2])


def test_check_epsilon_argument_type():
    arg = ("1e-3", [0.0001])
    for a in arg:
        with pytest.raises(TypeError):
            _check_epsilon()


def test_check_epsilon_argument_value():
    with pytest.raises(ValueError):
        _check_epsilon(-0.00001)


def test_check_epsilon():
    _check_epsilon(1e-2)
    _check_epsilon(0.001)


def test_check_gencost_argument_type(mock_grid):
    gencost_n = mock_grid.gencost["after"].copy()
    gencost_n.n = gencost_n.n.astype(float)
    arg = (1, gencost_n)
    for a in arg:
        with pytest.raises(TypeError):
            _check_gencost(a)


def test_check_gencost_argument_value(mock_grid):
    gencost = mock_grid.gencost["after"]
    gencost_n = mock_grid.gencost["after"].copy()
    gencost_n.loc[0, "n"] = 10
    gencost_type = mock_grid.gencost["after"].copy()
    gencost_type.loc[3, "type"] = 3
    arg = (
        gencost.drop(columns=["type"]),
        gencost.drop(columns=["n"]),
        gencost_type,
        gencost_n,
    )
    for a in arg:
        with pytest.raises(ValueError):
            _check_gencost(a)


def test_check_gencost(mock_grid):
    gencost = mock_grid.gencost["after"]
    _check_gencost(gencost)
