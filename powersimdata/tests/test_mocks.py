import numpy as np
import pandas as pd
import pytest

from powersimdata.tests.mock_grid import MockGrid
from powersimdata.tests.mock_profile_input import MockProfileInput
from powersimdata.tests.mock_scenario import MockScenario
from powersimdata.tests.mock_scenario_info import MockScenarioInfo

period_num = 4

# plant_id is the index
mock_plant = {
    "plant_id": [101, 102, 103, 104, 105, 106],
    "bus_id": [1001, 1002, 1003, 1004, 1005, 1006],
    "type": ["solar", "wind", "ng", "coal", "dfo", "hydro"],
    "zone_id": [1, 2, 3, 1, 3, 2],
    "GenFuelCost": [0, 0, 3.3, 4.4, 5.5, 0],
    "Pmin": [0, 0, 0, 0, 0, 0],
    "Pmax": [40, 80, 50, 150, 80, 60],
}


@pytest.fixture
def mock_pg():
    pg = pd.DataFrame(
        {
            plant_id: [(i + 1) * p for p in range(period_num)]
            for i, plant_id in enumerate(mock_plant["plant_id"])
        }
    )
    return pg


@pytest.fixture
def mock_solar(mock_pg):
    solar_plant_id = [
        plant_id
        for i, plant_id in enumerate(mock_plant["plant_id"])
        if mock_plant["type"][i] == "solar"
    ]
    return mock_pg[solar_plant_id] * 2


@pytest.fixture
def mock_wind(mock_pg):
    wind_plant_id = [
        plant_id
        for i, plant_id in enumerate(mock_plant["plant_id"])
        if mock_plant["type"][i] == "wind"
    ]
    return mock_pg[wind_plant_id] * 4


@pytest.fixture
def mock_hydro(mock_pg):
    hydro_plant_id = [
        plant_id
        for i, plant_id in enumerate(mock_plant["plant_id"])
        if mock_plant["type"][i] == "hydro"
    ]
    return mock_pg[hydro_plant_id] * 1.5


class TestMockGrid:
    def test_mock_grid_successes(self):
        grid = MockGrid(grid_attrs={"plant": mock_plant})
        assert isinstance(grid, object), "MockGrid should return an object"
        assert hasattr(grid, "plant"), "Plant property should be in the MockGrid"
        assert len(grid.branch) == 0, "Branch dataframe should be empty in the MockGrid"

    def test_mock_grid_failures(self):
        with pytest.raises(TypeError):
            MockGrid(grid_attrs="foo")
        with pytest.raises(TypeError):
            MockGrid(grid_attrs={1: "foo"})
        with pytest.raises(ValueError):
            MockGrid(grid_attrs={"foo": "bar"})


class TestMockScenario:
    def test_mock_pg_stored_properly(self, mock_pg):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, pg=mock_pg)
        pg = scenario.get_pg()
        err_msg = "pg should have dimension (periodNum * len(plant))"
        assert pg.shape == mock_pg.shape, err_msg

    def test_mock_solar_stored_properly(self, mock_solar):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, solar=mock_solar)
        solar = scenario.get_solar()
        err_msg = "solar should have dimension (periodNum * len(solar_plant))"
        assert solar.shape == mock_solar.shape, err_msg

    def test_mock_wind_stored_properly(self, mock_wind):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, wind=mock_wind)
        wind = scenario.get_wind()
        err_msg = "wind should have dimension (periodNum * len(wind_plant))"
        assert wind.shape == mock_wind.shape, err_msg

    def test_mock_hydro_stored_properly(self, mock_hydro):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, hydro=mock_hydro)
        hydro = scenario.get_hydro()
        err_msg = "hydro should have dimension (periodNum * len(hydro_plant))"
        assert hydro.shape == mock_hydro.shape, err_msg

    def test_mock_profile(self, mock_hydro, mock_solar, mock_wind):
        scenario = MockScenario(
            grid_attrs={"plant": mock_plant},
            hydro=mock_hydro,
            solar=mock_solar,
            wind=mock_wind,
        )
        pd.testing.assert_frame_equal(scenario.get_profile("hydro"), mock_hydro)
        pd.testing.assert_frame_equal(scenario.get_profile("solar"), mock_solar)
        pd.testing.assert_frame_equal(scenario.get_profile("wind"), mock_wind)

    def test_mock_profile_value(self):
        scenario = MockScenario(grid_attrs={"plant": mock_plant})
        with pytest.raises(ValueError):
            scenario.get_profile("coal")


class TestMockScenarioInfo:
    def test_create_mock_scenario_info(self):
        assert MockScenarioInfo() is not None

    def test_default_float(self):
        mock_s_info = MockScenarioInfo()
        assert 42 == mock_s_info.get_demand(1, 2, 3)

    def test_info_set_correctly(self):
        mock_s_info = MockScenarioInfo()
        mock_scenario = MockScenario()
        for k in mock_scenario.info.keys():
            assert k in mock_s_info.info.keys()

    def test_grid_set_correctly(self):
        mock_scenario = MockScenario()
        mock_s_info = MockScenarioInfo(mock_scenario)
        assert mock_scenario.get_grid() == mock_s_info.grid


class TestMockInputData:
    @pytest.fixture
    def grid(self):
        grid = MockGrid(grid_attrs={"plant": mock_plant})
        return grid

    def test_create_mock_profile_input(self, grid):
        assert MockProfileInput(grid) is not None

    def test_happy_case(self, grid):
        mock_profile_input = MockProfileInput(grid, periods=3)

        demand = mock_profile_input.get_data({}, "demand")
        expected_demand_values = np.array(
            [
                [0.355565, 0.453391, 0.563135],
                [0.873873, 0.342370, 0.766953],
                [0.802850, 0.125095, 0.150314],
            ]
        )
        expected_zone_ids = np.array([1, 2, 3])
        self._assert_profile(demand, expected_demand_values, expected_zone_ids)

        wind = mock_profile_input.get_data({}, "wind")
        expected_wind_values = np.array(
            [
                [0.460527],
                [0.054347],
                [0.278840],
            ]
        )
        expected_wind_plant_ids = np.array([102])
        self._assert_profile(wind, expected_wind_values, expected_wind_plant_ids)

        solar = mock_profile_input.get_data({}, "solar")
        expected_solar_values = np.array(
            [
                [0.305825],
                [0.219366],
                [0.091358],
            ]
        )
        expected_solar_plant_ids = np.array([101])
        self._assert_profile(solar, expected_solar_values, expected_solar_plant_ids)

        hydro = mock_profile_input.get_data({}, "hydro")
        expected_hydro_values = np.array(
            [
                [0.577557],
                [0.867702],
                [0.927690],
            ]
        )
        expected_hydro_plant_ids = np.array([106])
        self._assert_profile(hydro, expected_hydro_values, expected_hydro_plant_ids)

    def test_multiple_get_data_calls_returns_same_data(self, grid):
        mock_profile_input = MockProfileInput(grid)

        for type in ("demand", "wind", "solar", "hydro"):
            profile1 = mock_profile_input.get_data({}, type)
            profile2 = mock_profile_input.get_data({}, type)
            pd.testing.assert_frame_equal(profile1, profile2)

    def test_no_start_time(self, grid):
        mock_profile_input = MockProfileInput(
            grid, start_time=None, end_time="2016-01-01 02:00", periods=3, freq="H"
        )
        demand = mock_profile_input.get_data({}, "demand")
        self._assert_dates(demand.index)

    def test_no_end_time(self, grid):
        mock_profile_input = MockProfileInput(
            grid, start_time="2016-01-01 00:00", end_time=None, periods=3, freq="H"
        )
        demand = mock_profile_input.get_data({}, "demand")
        self._assert_dates(demand.index)

    def test_no_period(self, grid):
        mock_profile_input = MockProfileInput(
            grid,
            start_time="2016-01-01 00:00",
            end_time="2016-01-01 02:00",
            periods=None,
            freq="H",
        )
        demand = mock_profile_input.get_data({}, "demand")
        self._assert_dates(demand.index)

    def test_no_freq(self, grid):
        mock_profile_input = MockProfileInput(
            grid,
            start_time="2016-01-01 00:00",
            end_time="2016-01-01 02:00",
            periods=3,
            freq=None,
        )
        demand = mock_profile_input.get_data({}, "demand")
        self._assert_dates(demand.index)

    def test_raise_if_no_profile_specified(self, grid):
        with pytest.raises(ValueError) as exc:
            mock_profile_input = MockProfileInput(grid)
            mock_profile_input.get_data({}, "fusion")
        assert "No profile specified for fusion!" in str(exc.value)

    def test_raise_if_all_date_range_fields_present(self, grid):
        with pytest.raises(ValueError):
            MockProfileInput(
                grid,
                start_time="2016-01-01 00:00",
                end_time="2016-01-01 02:00",
                freq="H",
                periods=3,
            )

    def _assert_profile(self, profile, expected_values, expected_columns):
        np.testing.assert_almost_equal(profile.values, expected_values, decimal=5)
        np.testing.assert_almost_equal(profile.columns, expected_columns)
        self._assert_dates(profile.index)

    def _assert_dates(self, dates):
        expected_dates = pd.to_datetime(
            ["2016-01-01 00:00", "2016-01-01 01:00", "2016-01-01 02:00"]
        )
        np.testing.assert_array_equal(dates, expected_dates)
