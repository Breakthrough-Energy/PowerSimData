from powersimdata.design.scenario_info import ScenarioInfo
from powersimdata.tests.mock_scenario import MockScenario


class MockScenarioInfo(ScenarioInfo):
    def __init__(self, scenario=None):
        self._DEFAULT_FLOAT = 42
        scenario = MockScenario() if scenario is None else scenario
        super().__init__(scenario)

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
