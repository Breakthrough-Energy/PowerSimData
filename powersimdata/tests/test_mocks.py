import unittest

import pandas as pd

from powersimdata.tests.mock_scenario import MockScenario
from powersimdata.tests.mock_grid import MockGrid


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


class TestMocks(unittest.TestCase):
    def setUp(self):
        self.period_num = 4
        self.mock_pg = pd.DataFrame(
            {
                plant_id: [(i + 1) * p for p in range(self.period_num)]
                for i, plant_id in enumerate(mock_plant["plant_id"])
            }
        )
        self.mock_pg.set_index(
            pd.date_range(start="2016-01-01", periods=self.period_num, freq="H"),
            inplace=True,
        )
        self.mock_pg.index.name = "UTC"

        solar_plant_id = [
            plant_id
            for i, plant_id in enumerate(mock_plant["plant_id"])
            if mock_plant["type"][i] == "solar"
        ]
        self.mock_solar = self.mock_pg[solar_plant_id] * 2

        wind_plant_id = [
            plant_id
            for i, plant_id in enumerate(mock_plant["plant_id"])
            if mock_plant["type"][i] == "wind"
        ]
        self.mock_wind = self.mock_pg[wind_plant_id] * 4

        hydro_plant_id = [
            plant_id
            for i, plant_id in enumerate(mock_plant["plant_id"])
            if mock_plant["type"][i] == "hydro"
        ]
        self.mock_hydro = self.mock_pg[hydro_plant_id] * 1.5

    # check that MockGrid is working correctly
    def test_mock_grid_successes(self):
        grid = MockGrid(grid_attrs={"plant": mock_plant})
        self.assertTrue(isinstance(grid, object), "MockGrid should return an object")
        self.assertTrue(
            hasattr(grid, "plant"), "Plant property should be in the MockGrid"
        )
        self.assertEqual(
            len(grid.branch), 0, "Branch dataframe should be empty in the MockGrid"
        )

    def test_mock_grid_failures(self):
        with self.assertRaises(TypeError):
            MockGrid(grid_attrs="foo")
        with self.assertRaises(TypeError):
            MockGrid(grid_attrs={1: "foo"})
        with self.assertRaises(ValueError):
            MockGrid(grid_attrs={"foo": "bar"})

    def test_mock_pg_stored_properly(self):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, pg=self.mock_pg)
        pg = scenario.state.get_pg()
        err_msg = "pg should have dimension (periodNum * len(plant))"
        self.assertEqual(pg.shape, self.mock_pg.shape, err_msg)

    def test_mock_solar_stored_properly(self):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, solar=self.mock_solar)
        solar = scenario.state.get_solar()
        err_msg = "solar should have dimension (periodNum * len(solar_plant))"
        self.assertEqual(solar.shape, self.mock_solar.shape, err_msg)

    def test_mock_wind_stored_properly(self):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, wind=self.mock_wind)
        wind = scenario.state.get_wind()
        err_msg = "wind should have dimension (periodNum * len(wind_plant))"
        self.assertEqual(wind.shape, self.mock_wind.shape, err_msg)

    def test_mock_hydro_stored_properly(self):
        scenario = MockScenario(grid_attrs={"plant": mock_plant}, hydro=self.mock_hydro)
        hydro = scenario.state.get_hydro()
        err_msg = "hydro should have dimension (periodNum * len(hydro_plant))"
        self.assertEqual(hydro.shape, self.mock_hydro.shape, err_msg)


if __name__ == "__main__":
    unittest.main()
