from postreise.process import const
from postreise.process.transferdata import PullData
from powersimdata.scenario.analyze import Analyze
from powersimdata.scenario.create import Create
from powersimdata.scenario.delete import Delete
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

        if not descriptor:
            self.state = Create()
        else:
            self._get_info(descriptor)
            try:
                state = self._info['state']
                self._get_status()
                if state == 'execute':
                    self.state = Execute(self)
                elif state == 'analyze':
                    self.state = Analyze(self)
            except:
                pass

    def _get_info(self, descriptor):
        """Gets scenario information

        :param str descriptor: scenario descriptor.
        """
        td = PullData()
        table = td.get_scenario_table()

        def not_found_message(table):
            """Print message when scenario is not found.

            :param pandas table: scenario table.
            """
            print("------------------")
            print("SCENARIO NOT FOUND")
            print("------------------")
            print(table.tail(n=10).to_string(index=False, justify='center',
                                             columns=['id', 'plan', 'name',
                                                      'interconnect',
                                                      'base_demand',
                                                      'base_hydro',
                                                      'base_solar',
                                                      'base_wind']))

        try:
            int(descriptor)
            scenario = table[table.id == descriptor]
            if scenario.shape[0] == 0:
                not_found_message(table)
            else:
                self._info = scenario.to_dict('records', into=OrderedDict)[0]
            return
        except ValueError:
            scenario = table[table.name == descriptor]
            if scenario.shape[0] == 0:
                not_found_message(table)
            elif scenario.shape[0] == 1:
                self._info = scenario.to_dict('records', into=OrderedDict)[0]
            elif scenario.shape[0] > 1:
                print("-----------------------")
                print("MULTIPLE SCENARIO FOUND")
                print("-----------------------")
                print('Use id to access scenario')
                print(table.to_string(index=False, justify='center',
                                      columns=['id', 'plan', 'name',
                                               'interconnect',
                                               'base_demand',
                                               'base_hydro',
                                               'base_solar',
                                               'base_wind']))
            return

    def _get_status(self):
        """Get execution status of scenario.

        :raises Exception: if scenario not found in execute list on server.
        """
        td = PullData()
        table = td.get_execute_table()

        status = table[table.id == self._info['id']]
        if status.shape[0] == 0:
            raise Exception("Scenario not found in %s on server" %
                             const.EXECUTE_DIR)
        elif status.shape[0] == 1:
            self._status = status.status.values[0]

    def print_scenario_info(self):
        """Prints scenario information.

        """
        self.state.print_scenario_info()

    def change(self, state):
      """Changes state.

      :param class state: One of the sub-classes.
      """
      self.state.switch(state)
