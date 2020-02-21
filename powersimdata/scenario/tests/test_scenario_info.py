import unittest
import pandas as pd

from powersimdata.scenario.scenario_info import ScenarioInfo
from postreise.tests.mock_scenario import MockScenario

mock_plant = {
    'plant_id': [101, 102, 103, 104, 105, 106],
    'bus_id': [1001, 1002, 1003, 1004, 1005, 1006],
    'type': ['solar', 'wind', 'ng', 'coal', 'dfo', 'hydro'],
    'zone_name': ['zone1', 'zone1', 'zone1', 'zone1', 'zone1', 'zone1'],
    'GenFuelCost': [0, 0, 3.3, 4.4, 5.5, 0],
    'Pmin': [0, 0, 0, 0, 0, 0],
    'Pmax': [40, 80, 50, 150, 80, 60],
}

period_num = 4
mock_pg = pd.DataFrame({
    plant_id: [(i + 1) * p for p in range(period_num)]
    for i, plant_id in enumerate(mock_plant['plant_id'])})
mock_pg.set_index(pd.date_range(
    start='2016-01-01', periods=period_num, freq='H'),
    inplace=True)
mock_pg.index.name = 'UTC'

solar_plant_id = [plant_id
                  for i, plant_id in enumerate(mock_plant['plant_id'])
                  if mock_plant['type'][i] == 'solar']
wind_plant_id = [plant_id
                 for i, plant_id in enumerate(mock_plant['plant_id'])
                 if mock_plant['type'][i] == 'wind']
ng_plant_id = [plant_id
               for i, plant_id in enumerate(mock_plant['plant_id'])
               if mock_plant['type'][i] == 'ng']
coal_plant_id = [plant_id
                 for i, plant_id in enumerate(mock_plant['plant_id'])
                 if mock_plant['type'][i] == 'coal']
dfo_plant_id = [plant_id
                for i, plant_id in enumerate(mock_plant['plant_id'])
                if mock_plant['type'][i] == 'dfo']
hydro_plant_id = [plant_id
                  for i, plant_id in enumerate(mock_plant['plant_id'])
                  if mock_plant['type'][i] == 'hydro']

mock_solar = mock_pg[solar_plant_id] * 2
mock_wind = mock_pg[wind_plant_id] * 4
mock_hydro = mock_pg[hydro_plant_id] * 1.5

start_time = '2016-01-01 00:00:00'
end_time = '2016-01-01 03:00:00'


class TestScenarioInfo(unittest.TestCase):

    def setUp(self):
        scenario = MockScenario(grid_attrs={'plant': mock_plant},
                                pg=mock_pg, solar=mock_solar,
                                wind=mock_wind, hydro=mock_hydro)
        self.scenario_info = ScenarioInfo(scenario)

    def test_get_capacity(self):
        assert self.scenario_info.get_capacity('solar', 'all') == 40
        assert self.scenario_info.get_capacity('wind', 'all') == 80
        assert self.scenario_info.get_capacity('ng', 'all') == 50
        assert self.scenario_info.get_capacity('coal', 'all') == 150
        assert self.scenario_info.get_capacity('dfo', 'all') == 80
        assert self.scenario_info.get_capacity('hydro', 'all') == 60

    def test_get_generation(self):
        assert self.scenario_info.get_generation\
        ('solar', 'all', start_time, end_time) == \
            mock_pg[solar_plant_id].sum().sum()
        assert self.scenario_info.get_generation\
        ('wind', 'all', start_time, end_time) == \
            mock_pg[wind_plant_id].sum().sum()
        assert self.scenario_info.get_generation\
        ('ng', 'all', start_time, end_time) == \
            mock_pg[ng_plant_id].sum().sum()
        assert self.scenario_info.get_generation\
        ('coal', 'all', start_time, end_time) == \
            mock_pg[coal_plant_id].sum().sum()
        assert self.scenario_info.get_generation\
        ('dfo', 'all', start_time, end_time) == \
            mock_pg[dfo_plant_id].sum().sum()
        assert self.scenario_info.get_generation\
        ('hydro', 'all', start_time, end_time) == \
            mock_pg[hydro_plant_id].sum().sum()

    def test_get_curtailment(self):
        assert self.scenario_info.get_curtailment\
        ('solar', 'all', start_time, end_time) == \
            round(1 - (mock_pg[solar_plant_id].sum().sum()
                       / mock_solar.sum().sum()), 4)
        assert self.scenario_info.get_curtailment\
        ('wind', 'all', start_time, end_time) == \
            round(1 - (mock_pg[wind_plant_id].sum().sum()
                       / mock_wind.sum().sum()), 4)
        assert self.scenario_info.get_curtailment\
        ('hydro', 'all', start_time, end_time) == \
            round(1 - (mock_pg[hydro_plant_id].sum().sum()
                       / mock_hydro.sum().sum()), 4)

    def test_get_profile_resource(self):
        assert self.scenario_info.get_profile_resource\
        ('solar', 'all', start_time, end_time)\
            == mock_solar.sum().sum()
        assert self.scenario_info.get_profile_resource\
        ('wind', 'all', start_time, end_time)\
            == mock_wind.sum().sum()
        assert self.scenario_info.get_profile_resource\
        ('hydro', 'all', start_time, end_time)\
            == mock_hydro.sum().sum()

    def test_get_capacity_factor(self):
        assert self.scenario_info.get_capacity_factor\
        ('solar', 'all', start_time, end_time) \
            == round(mock_pg[solar_plant_id].sum().sum() /
                     (40 * period_num), 4)
        assert self.scenario_info.get_capacity_factor\
        ('wind', 'all', start_time, end_time) \
            == round(mock_pg[wind_plant_id].sum().sum() /
                     (80 * period_num), 4)
        assert self.scenario_info.get_capacity_factor\
        ('ng', 'all', start_time, end_time) \
            == round(mock_pg[ng_plant_id].sum().sum() /
                     (50 * period_num), 4)
        assert self.scenario_info.get_capacity_factor\
        ('coal', 'all', start_time, end_time) \
            == round(mock_pg[coal_plant_id].sum().sum() /
                     (150 * period_num), 4)
        assert self.scenario_info.get_capacity_factor\
        ('dfo', 'all', start_time, end_time) \
            == round(mock_pg[dfo_plant_id].sum().sum() /
                     (80 * period_num), 4)
        assert self.scenario_info.get_capacity_factor\
        ('hydro', 'all', start_time, end_time) \
            == round(mock_pg[hydro_plant_id].sum().sum() /
                     (60 * period_num), 4)

    def test_get_no_congest_capacity_factor(self):
        assert self.scenario_info.get_no_congest_capacity_factor\
        ('solar', 'all', start_time, end_time) == round(
            mock_solar.sum().sum() / (40 * period_num), 4)
        assert self.scenario_info.get_no_congest_capacity_factor\
        ('wind', 'all', start_time, end_time) == round(
            mock_wind.sum().sum() / (80 * period_num), 4)
        assert self.scenario_info.get_no_congest_capacity_factor\
        ('hydro', 'all', start_time, end_time) == round(
            mock_hydro.sum().sum() / (60 * period_num), 4)
