import pandas as pd
import pytest

from powersimdata.tests.mock_grid import MockGrid
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
        pg = scenario.state.get_pg()
        err_msg = "pg should have dimension (periodNum * len(plant))"
        assert pg.shape == mock_pg.shape, err_msg

    def test_mock_solar_stored_properly(self, mock_solar):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, solar=mock_solar)
        solar = scenario.state.get_solar()
        err_msg = "solar should have dimension (periodNum * len(solar_plant))"
        assert solar.shape == mock_solar.shape, err_msg

    def test_mock_wind_stored_properly(self, mock_wind):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, wind=mock_wind)
        wind = scenario.state.get_wind()
        err_msg = "wind should have dimension (periodNum * len(wind_plant))"
        assert wind.shape == mock_wind.shape, err_msg

    def test_mock_hydro_stored_properly(self, mock_hydro):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, hydro=mock_hydro)
        hydro = scenario.state.get_hydro()
        err_msg = "hydro should have dimension (periodNum * len(hydro_plant))"
        assert hydro.shape == mock_hydro.shape, err_msg


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
        assert mock_scenario.state.get_grid() == mock_s_info.grid
