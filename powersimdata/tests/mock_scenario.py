from powersimdata.scenario.scenario import Scenario
from powersimdata.tests.mock_analyze import MockAnalyze


class MockScenario:
    """
    :param dict grid_attrs: fields to be added to grid.
    :param \\*\\*kwargs: collected keyword arguments to be passed to
        MockAnalyze init.
    """

    _setattr_allowlist = {"state", "info"}

    def __init__(self, grid_attrs=None, **kwargs):
        """Constructor."""
        self.state = MockAnalyze(grid_attrs, **kwargs)
        self.info = {
            "id": "111",
            "plan": None,
            "name": None,
            "state": None,
            "grid_model": "usa_tamu",
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

    def __dir__(self):
        return sorted(super().__dir__() + list(self.state.exported_methods))

    def __getattr__(self, name):
        if name in self.state.exported_methods:
            return getattr(self.state, name)
        elif hasattr(self.state, "__getattr__"):
            return self.state.__getattr__(name)
        else:
            raise AttributeError(
                f"Scenario object in {self.state.name} state "
                f"has no attribute {name}"
            )

    def __setattr__(self, name, value):
        if name in self._setattr_allowlist:
            super().__setattr__(name, value)
        elif name in self.state.exported_methods:
            raise AttributeError(
                f"{name} is exported from Scenario.state, edit it there if necessary"
            )
        super().__setattr__(name, value)
