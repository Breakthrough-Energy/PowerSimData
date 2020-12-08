from collections import OrderedDict

import pandas as pd

from powersimdata.data_access.context import Context
from powersimdata.data_access.execute_list import ExecuteListManager
from powersimdata.data_access.scenario_list import ScenarioListManager
from powersimdata.scenario.analyze import Analyze
from powersimdata.scenario.create import Create
from powersimdata.scenario.execute import Execute
from powersimdata.utility import server_setup

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
        scenario_table = self._scenario_list_manager.get_scenario_table()

        def err_message(table, text):
            """Print message when scenario is not found or multiple matches are
            found.

            :param pandas.DataFrame table: scenario table.
            :param str text: message to print.
            """
            print(
                table.to_string(
                    index=False,
                    justify="center",
                    columns=[
                        "id",
                        "plan",
                        "name",
                        "interconnect",
                        "base_demand",
                        "base_hydro",
                        "base_solar",
                        "base_wind",
                    ],
                )
            )
            print("------------------")
            print(text)
            print("------------------")

        try:
            int(descriptor)
            scenario = scenario_table[scenario_table.id == descriptor]
        except ValueError:
            scenario = scenario_table[scenario_table.name == descriptor]
            if scenario.shape[0] > 1:
                err_message(scenario, "MULTIPLE SCENARIO FOUND")
                print("Use id to access scenario")

        if scenario.shape[0] == 0:
            err_message(scenario_table, "SCENARIO NOT FOUND")
        elif scenario.shape[0] == 1:
            self.info = scenario.to_dict("records", into=OrderedDict)[0]

    def _set_status(self):
        """Sets execution status of scenario.

        :raises Exception: if scenario not found in execute list on server.
        """
        execute_table = self._execute_list_manager.get_execute_table()

        status = execute_table[execute_table.id == self.info["id"]]
        if status.shape[0] == 0:
            raise Exception(
                "Scenario not found in %s on server" % server_setup.EXECUTE_LIST
            )
        elif status.shape[0] == 1:
            self.status = status.status.values[0]

    def print_scenario_info(self):
        """Prints scenario information."""
        self.state.print_scenario_info()

    def change(self, state):
        """Changes state.

        :param class state: One of :class:`.Analyze` :class:`.Create`,
            :class:`.Execute` or :class:`.Delete`.
        """
        self.state.switch(state)
