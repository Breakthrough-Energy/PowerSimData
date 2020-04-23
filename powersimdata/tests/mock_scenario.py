from powersimdata.scenario.scenario import Scenario
from powersimdata.tests.mock_analyze import MockAnalyze


class MockScenario:
    def __init__(self, grid_attrs, **kwargs):
        """Constructor.

        :param dict grid_attrs: fields to be added to grid.
        :param pandas.DataFrame pg: dummy pg
        """
        self.state = MockAnalyze(grid_attrs, **kwargs)
        self.info = {id: '111'}

    @property
    def __class__(self):
        """If anyone asks, I'm a Scenario object!"""
        return Scenario
