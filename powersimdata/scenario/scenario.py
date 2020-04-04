from powersimdata.utility import const
from powersimdata.utility.transfer_data import (setup_server_connection,
                                                get_scenario_table,
                                                get_execute_table)
from powersimdata.scenario.analyze import Analyze
from powersimdata.scenario.create import Create
from powersimdata.scenario.execute import Execute

from collections import OrderedDict

import pandas as pd
pd.set_option('display.max_colwidth', -1)


class Scenario(object):
    """Handles scenario.

    :param str descriptor: scenario name or index.
    """

    def __init__(self, descriptor):
        """Constructor.

        """
        if not isinstance(descriptor, str):
            raise TypeError('Descriptor must be a string')

        self.ssh = setup_server_connection()
        if not descriptor:
            self.state = Create(self)
        else:
            self._set_info(descriptor)
            try:
                state = self.info['state']
                self._set_status()
                if state == 'execute':
                    self.state = Execute(self)
                elif state == 'analyze':
                    self.state = Analyze(self)
            except AttributeError:
                return

    def _set_info(self, descriptor):
        """Sets scenario information.

        :param str descriptor: scenario descriptor.
        """
        scenario_table = get_scenario_table(self.ssh)

        def not_found_message(table):
            """Print message when scenario is not found.

            :param pandas table: scenario table.
            """
            print("------------------")
            print("SCENARIO NOT FOUND")
            print("------------------")
            print(table.to_string(index=False, justify='center',
                                  columns=['id', 'plan', 'name', 'interconnect',
                                           'base_demand', 'base_hydro',
                                           'base_solar', 'base_wind']))

        try:
            int(descriptor)
            scenario = scenario_table[scenario_table.id == descriptor]
            if scenario.shape[0] == 0:
                not_found_message(scenario_table)
            else:
                self.info = scenario.to_dict('records', into=OrderedDict)[0]
            return
        except ValueError:
            scenario = scenario_table[scenario_table.name == descriptor]
            if scenario.shape[0] == 0:
                not_found_message(scenario_table)
            elif scenario.shape[0] == 1:
                self.info = scenario.to_dict('records', into=OrderedDict)[0]
            elif scenario.shape[0] > 1:
                print("-----------------------")
                print("MULTIPLE SCENARIO FOUND")
                print("-----------------------")
                print('Use id to access scenario')
                print(scenario_table.to_string(index=False, justify='center',
                                               columns=['id', 'plan', 'name',
                                                        'interconnect',
                                                        'base_demand',
                                                        'base_hydro',
                                                        'base_solar',
                                                        'base_wind']))
            return

    def _set_status(self):
        """Sets execution status of scenario.

        :raises Exception: if scenario not found in execute list on server.
        """
        execute_table = get_execute_table(self.ssh)

        status = execute_table[execute_table.id == self.info['id']]
        if status.shape[0] == 0:
            raise Exception("Scenario not found in %s on server" %
                            const.EXECUTE_LIST)
        elif status.shape[0] == 1:
            self.status = status.status.values[0]

    def print_scenario_info(self):
        """Prints scenario information.

        """
        self.state.print_scenario_info()

    def change(self, state):
        """Changes state.

        :param class state: One of :class:`.Analyze` :class:`.Create`,
            :class:`.Execute` or :class:`.Delete`.
        """
        self.state.switch(state)
