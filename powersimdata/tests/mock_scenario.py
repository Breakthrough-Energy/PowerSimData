from powersimdata.scenario.scenario import Scenario
from powersimdata.tests.mock_analyze import MockAnalyze


class MockScenario:
    def __init__(self, grid_attrs=None, **kwargs):
        """Constructor.

        :param dict grid_attrs: fields to be added to grid.
        :param pandas.DataFrame pg: dummy pg
        """
        self.state = MockAnalyze(grid_attrs, **kwargs)
        self.info = {
            "id": "111",
            "plan": None,
            "name": None,
            "state": None,
            "interconnect": None,
            "base_demand": None,
            "base_hydro": None,
            "base_solar": None,
            "base_wind": None,
            "change_table": None,
            "start_date": None,
            "end_date": None,
            "interval": None,
            "engine": None,
            "runtime": None,
            "infeasibilities": None,
        }

    @property
    def __class__(self):
        """If anyone asks, I'm a Scenario object!"""
        return Scenario
