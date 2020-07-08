from powersimdata.design.scenario_info import ScenarioInfo
from powersimdata.tests.mock_grid import MockGrid
from powersimdata.tests.mock_scenario import MockScenario


class MockScenarioInfo(ScenarioInfo):
    def __init__(self, mock_scenario=None, mock_grid=None):
        self._DEFAULT_FLOAT = 42
        self.grid = mock_grid or MockGrid()
        self._set_info(mock_scenario)

    def _set_info(self, scenario):
        if scenario is None:
            scenario = MockScenario()
        self.info = scenario.info

    def area_to_loadzone(self, area, area_type=None):
        return set()

    def get_available_resource(self, area, area_type=None):
        return []

    def get_demand(self, area, start_time, end_time, area_type=None):
        return self._DEFAULT_FLOAT

    def get_capacity(self, gentype, area, area_type=None):
        return self._DEFAULT_FLOAT

    def get_generation(self, gentype, area, start_time, end_time, area_type=None):
        return self._DEFAULT_FLOAT

    def get_profile_resource(self, gentype, area, start_time, end_time, area_type=None):
        return self._DEFAULT_FLOAT

    def get_curtailment(self, gentype, area, start_time, end_time, area_type=None):
        return self._DEFAULT_FLOAT

    def get_capacity_factor(self, gentype, area, start_time, end_time, area_type=None):
        return self._DEFAULT_FLOAT

    def get_no_congest_capacity_factor(
        self, gentype, area, start_time, end_time, area_type=None
    ):
        return self._DEFAULT_FLOAT
