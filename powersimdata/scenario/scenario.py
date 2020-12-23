import pandas as pd

from powersimdata.data_access.context import Context
from powersimdata.data_access.execute_list import ExecuteListManager
from powersimdata.data_access.scenario_list import ScenarioListManager
from powersimdata.scenario.analyze import Analyze
from powersimdata.scenario.create import Create
from powersimdata.scenario.execute import Execute

pd.set_option("display.max_colwidth", None)


class Scenario(object):
    """Handles scenario.

    :param int/str descriptor: scenario name or index.
    """

    def __init__(self, descriptor):
        """Constructor."""
        if isinstance(descriptor, int):
            descriptor = str(descriptor)
        if not isinstance(descriptor, str):
            raise TypeError("Descriptor must be a string or int (for a Scenario ID)")

        self.data_access = Context.get_data_access()
        self._scenario_list_manager = ScenarioListManager(self.data_access)
        self._execute_list_manager = ExecuteListManager(self.data_access)

        if not descriptor:
            self.state = Create(self)
        else:
            self._set_info(descriptor)
            try:
                state = self.info["state"]
                self._set_status()
                if state == "execute":
                    self.state = Execute(self)
                elif state == "analyze":
                    self.state = Analyze(self)
            except AttributeError:
                return

    def _set_info(self, descriptor):
        """Sets scenario information.

        :param str descriptor: scenario descriptor.
        """
        info = self._scenario_list_manager.get_scenario(descriptor)
        if info is not None:
            self.info = info

    def _set_status(self):
        """Sets execution status of scenario."""
        scenario_id = self.info["id"]
        self.status = self._execute_list_manager.get_status(scenario_id)

    def print_scenario_info(self):
        """Prints scenario information."""
        self.state.print_scenario_info()

    def change(self, state):
        """Changes state.

        :param class state: One of :class:`.Analyze` :class:`.Create`,
            :class:`.Execute` or :class:`.Delete`.
        """
        self.state.switch(state)
