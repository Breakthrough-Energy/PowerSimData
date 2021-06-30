import unittest

import pandas as pd
import pytest
from numpy.testing import assert_array_almost_equal, assert_array_equal

from powersimdata.input.grid import Grid
from powersimdata.input.helpers import (
    get_active_resources_in_grid,
    get_plant_id_for_resources,
    get_plant_id_for_resources_in_area,
    get_plant_id_for_resources_in_interconnects,
    get_plant_id_for_resources_in_loadzones,
    get_plant_id_for_resources_in_states,
    get_plant_id_in_interconnects,
    get_plant_id_in_loadzones,
    get_plant_id_in_states,
    get_resources_in_grid,
    get_storage_id_in_area,
    summarize_plant_to_bus,
    summarize_plant_to_location,
)
from powersimdata.tests.mock_grid import MockGrid
from powersimdata.tests.mock_scenario import MockScenario

# plant_id is the index
mock_plant = {
    "plant_id": ["A", "B", "C", "D"],
    "bus_id": [1, 1, 2, 3],
    "lat": [47.6, 47.6, 37.8, 37.8],
    "lon": [-122.3, -122.3, -122.4, -122.4],
    "type": ["coal", "ng", "coal", "solar"],
    "Pmin": [0, 50, 0, 0],
    "Pmax": [0, 300, 0, 50],
    "zone_name": ["Washington", "Washington", "Bay Area", "Bay Area"],
}

# bus_id is the index
mock_bus = {
    "bus_id": [1, 2, 3, 4],
    "lat": [47.6, 37.8, 37.8, 40.7],
    "lon": [-122.3, -122.4, -122.4, -74],
    "zone_id": [201, 204, 204, 7],
}

mock_pg = pd.DataFrame(
    {
        "A": [1, 2, 3, 4],
        "B": [1, 2, 4, 8],
        "C": [1, 1, 2, 3],
        "D": [1, 3, 5, 7],
    }
)

mock_storage = {
    "bus_id": [1, 2, 3],
    "Pmax": [10, 10, 10],
}

grid_attrs = {"plant": mock_plant, "bus": mock_bus, "storage_gen": mock_storage}
scenario = MockScenario(grid_attrs)
scenario.state.grid.zone2id = {
    "Washington": 201,
    "Bay Area": 204,
    "New York City": 7,
}


def check_dataframe_matches(received_return, expected_return):
    assert isinstance(received_return, pd.DataFrame)
    assert_array_equal(
        received_return.index.to_numpy(), expected_return.index.to_numpy()
    )
    assert_array_equal(
        received_return.columns.to_numpy(), expected_return.columns.to_numpy()
    )
    assert_array_almost_equal(received_return.to_numpy(), expected_return.to_numpy())


class TestSummarizePlantToBus(unittest.TestCase):
    def setUp(self):
        self.grid = MockGrid(grid_attrs)

    def test_summarize_default(self):
        expected_return = pd.DataFrame(
            {
                1: [2, 4, 7, 12],
                2: [1, 1, 2, 3],
                3: [1, 3, 5, 7],
            }
        )
        bus_data = summarize_plant_to_bus(mock_pg, self.grid)
        check_dataframe_matches(bus_data, expected_return)

    def test_summarize_all_buses_false(self):
        expected_return = pd.DataFrame(
            {
                1: [2, 4, 7, 12],
                2: [1, 1, 2, 3],
                3: [1, 3, 5, 7],
            }
        )
        bus_data = summarize_plant_to_bus(mock_pg, self.grid, all_buses=False)
        check_dataframe_matches(bus_data, expected_return)

    def test_summarize_all_buses_true(self):
        expected_return = pd.DataFrame(
            {
                1: [2, 4, 7, 12],
                2: [1, 1, 2, 3],
                3: [1, 3, 5, 7],
                4: [0, 0, 0, 0],
            }
        )
        bus_data = summarize_plant_to_bus(mock_pg, self.grid, all_buses=True)
        check_dataframe_matches(bus_data, expected_return)


class TestSummarizePlantToLocation(unittest.TestCase):
    def setUp(self):
        self.grid = MockGrid(grid_attrs)

    def _check_dataframe_matches(self, loc_data, expected_return):
        self.assertIsInstance(loc_data, pd.DataFrame)
        assert_array_equal(loc_data.index.to_numpy(), expected_return.index.to_numpy())
        self.assertEqual(
            set(loc_data.columns.to_numpy()), set(expected_return.columns.to_numpy())
        )
        for c in loc_data.columns:
            assert_array_almost_equal(
                loc_data[c].to_numpy(), expected_return[c].to_numpy()
            )

    def test_summarize_location(self):
        expected_return = pd.DataFrame(
            {
                (47.6, -122.3): [2, 4, 7, 12],
                (37.8, -122.4): [2, 4, 7, 10],
            }
        )
        loc_data = summarize_plant_to_location(mock_pg, self.grid)
        self._check_dataframe_matches(loc_data, expected_return)


class TestResourcesInGrid(unittest.TestCase):
    def setUp(self):
        self.grid = MockGrid(grid_attrs)

    def test_get_resources_in_grid(self):
        assert get_resources_in_grid(self.grid) == {"ng", "coal", "solar"}

    def test_get_active_resources_in_grid(self):
        assert get_active_resources_in_grid(self.grid) == {"ng", "solar"}


@pytest.fixture(scope="module")
def grid():
    return Grid(["USA"])


def test_get_plant_id_for_resources_argument_type(grid):
    arg = ((1, grid), ([1, 2, 3], grid), ("nuclear", 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_plant_id_for_resources(a[0], a[1])


def test_get_plant_id_for_resources_argument_value(grid):
    arg = (("uranium", grid), (["uranium", "plutonium"], grid))
    for a in arg:
        with pytest.raises(ValueError):
            get_plant_id_for_resources(a[0], a[1])


def test_get_plant_id_for_resources(grid):
    arg = (("nuclear", grid), (["solar", "ng"], grid))
    expected = (["nuclear"], ["solar", "ng"])
    for a, e in zip(arg, expected):
        plant_id = get_plant_id_for_resources(a[0], a[1])
        assert set(grid.plant.loc[plant_id].type) == set(e)


def test_get_plant_id_in_loadzones_argument_type(grid):
    arg = ((1, grid), ([1, 2, 3], grid), ("Nevada", 1), ("Far West", 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_plant_id_in_loadzones(a[0], a[1])


def test_get_plant_id_in_loadzones_argument_value(grid):
    arg = (("France", grid), (["Alberta", "British Columbia"], grid))
    for a in arg:
        with pytest.raises(ValueError):
            get_plant_id_in_loadzones(a[0], a[1])


def test_get_plant_id_in_loadzones(grid):
    arg = (("Oregon", grid), (["Kentucky", "Montana Western", "El Paso"], grid))
    expected = (["Oregon"], ["Kentucky", "Montana Western", "El Paso"])
    for a, e in zip(arg, expected):
        plant_id = get_plant_id_in_loadzones(a[0], a[1])
        assert set(grid.plant.loc[plant_id].zone_name) == set(e)


def test_get_plant_id_in_interconnects_argument_type(grid):
    arg = ((1, grid), ([1, 2, 3], grid), ("Eastern", 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_plant_id_in_interconnects(a[0], a[1])


def test_get_plant_id_in_interconnects_argument_value(grid):
    arg = (("ERCOT", grid), (["CAISO", "Western"], grid))
    for a in arg:
        with pytest.raises(ValueError):
            get_plant_id_in_interconnects(a[0], a[1])


def test_get_plant_id_in_interconnects(grid):
    arg = (("Western", grid), (["Texas_Western", "Eastern"], grid))
    expected = (["Western"], ["Texas", "Western", "Eastern"])
    for a, e in zip(arg, expected):
        plant_id = get_plant_id_in_interconnects(a[0], a[1])
        assert set(grid.plant.loc[plant_id].interconnect) == set(e)


def test_get_plant_id_in_states_argument_type(grid):
    arg = ((1, grid), ([1, 2, 3], grid), ("California", 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_plant_id_in_states(a[0], a[1])


def test_get_plant_id_in_states_argument_value(grid):
    arg = (("Western", grid), (["Far West", "New Mexico Eastern"], grid))
    for a in arg:
        with pytest.raises(ValueError):
            get_plant_id_in_states(a[0], a[1])


def test_get_plant_id_in_states(grid):
    arg = (("TX", grid), (["Washington", "OR", "Idaho"], grid))
    expected = (({44, 45, 216} | set(range(301, 309))), {201, 202, 214})
    for a, e in zip(arg, expected):
        plant_id = get_plant_id_in_states(a[0], a[1])
        assert set(grid.plant.loc[plant_id].zone_id) == e


def test_get_plant_id_for_resources_in_loadzones_argument_type(grid):
    arg = ((1, 1, grid), ([1, 2, 3], {4, 5, 5}, grid), ("solar", "Utah", 1))
    for a in arg:
        with pytest.raises(TypeError):
            get_plant_id_for_resources_in_loadzones(a[0], a[1], a[2])


def test_get_plant_id_for_resources_in_loadzones_argument_value(grid):
    arg = (
        (["solar", "hydro", "wind"], "Western", grid),
        ("plutonium", "Kentucky", grid),
    )
    for a in arg:
        with pytest.raises(ValueError):
            get_plant_id_for_resources_in_loadzones(a[0], a[1], a[2])


def test_get_plant_id_for_resources_in_loadzones(grid):
    arg = (
        ("solar", ["Utah", "Montana Western"], grid),
        (["nuclear", "wind"], ["Colorado", "El Paso"], grid),
        (["wind", "solar"], "Oregon", grid),
        (["coal", "ng"], ["South Carolina", "Ohio River", "Maine"], grid),
    )
    expected = (
        (["solar"], ["Utah"]),
        (["wind"], ["Colorado"]),
        (["wind", "solar"], ["Oregon"]),
        (["coal", "ng"], ["South Carolina", "Ohio River", "Maine"]),
    )
    for a, e in zip(arg, expected):
        plant_id = get_plant_id_for_resources_in_loadzones(a[0], a[1], a[2])
        assert set(grid.plant.loc[plant_id].type) == set(e[0])
        assert set(grid.plant.loc[plant_id].zone_name) == set(e[1])


def test_get_plant_id_for_resources_in_interconnects_argument_type(grid):
    arg = (
        (1, 1, grid),
        ([1, 2, 3], {4, 5, 5}, grid),
        (["solar", "ng", "gothermal"], "Texas_Western", 1),
    )
    for a in arg:
        with pytest.raises(TypeError):
            get_plant_id_for_resources_in_interconnects(a[0], a[1], a[2])


def test_get_plant_id_for_resources_in_interconnects_argument_value(grid):
    arg = (
        (["nuclear", "hydro"], "coal", grid),
        (["plutonium", "coal"], ["Eastern", "Texas"], grid),
    )
    for a in arg:
        with pytest.raises(ValueError):
            get_plant_id_for_resources_in_interconnects(a[0], a[1], a[2])


def test_get_plant_id_for_resources_in_interconnects(grid):
    arg = (
        ("solar", ["Western"], grid),
        (["nuclear", "wind"], ["Texas_Western"], grid),
        (["geothermal"], ["Western", "Eastern"], grid),
    )
    expected = (
        (["solar"], ["Western"]),
        (["nuclear", "wind"], ["Texas", "Western"]),
        (["geothermal"], ["Western"]),
    )
    for a, e in zip(arg, expected):
        plant_id = get_plant_id_for_resources_in_interconnects(a[0], a[1], a[2])
        assert set(grid.plant.loc[plant_id].type) == set(e[0])
        assert set(grid.plant.loc[plant_id].interconnect) == set(e[1])


def test_get_plant_id_for_resources_in_states_argument_type(grid):
    arg = (
        (1, 1, grid),
        ([1, 2, 3], {4, 5, 5}, grid),
        (["solar", "ng", "gothermal"], ["New Mexico", "California"], 1),
    )
    for a in arg:
        with pytest.raises(TypeError):
            get_plant_id_for_resources_in_states(a[0], a[1], a[2])


def test_get_plant_id_for_resources_in_states_argument_value(grid):
    arg = (
        (["nuclear", "hydro"], "Eastern", grid),
        (["plutonium", "coal"], ["Illinois", "FL"], grid),
    )
    for a in arg:
        with pytest.raises(ValueError):
            get_plant_id_for_resources_in_states(a[0], a[1], a[2])


def test_get_plant_id_for_resources_in_states(grid):
    arg = (
        (["solar", "wind", "nuclear"], ["California", "TX"], grid),
        (["nuclear", "wind"], ["Washington"], grid),
        (["geothermal"], ["Nevada", "Massachusetts", "Mississippi"], grid),
    )
    expected = (
        (
            ["solar", "wind", "nuclear"],
            set(range(203, 208)) | {44, 45, 216} | set(range(301, 309)),
        ),
        (["nuclear", "wind"], [201]),
        (["geothermal"], [208]),
    )
    for a, e in zip(arg, expected):
        plant_id = get_plant_id_for_resources_in_states(a[0], a[1], a[2])
        assert set(grid.plant.loc[plant_id].type) == set(e[0])
        assert set(grid.plant.loc[plant_id].zone_id) == set(e[1])


def test_get_plant_id_for_resources_in_area():
    arg = [(scenario, "Washington", "coal"), (scenario, "all", "coal")]
    expected = [["A"], ["A", "C"]]
    for a, e in zip(arg, expected):
        plant_id = get_plant_id_for_resources_in_area(*a)
        assert e == plant_id


def test_get_storage_id_in_area():
    arg = [(scenario, "Bay Area"), (scenario, "all")]
    expected = [[1, 2], [0, 1, 2]]
    for a, e in zip(arg, expected):
        storage_id = get_storage_id_in_area(*a)
        assert e == storage_id
