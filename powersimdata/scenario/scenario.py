from postreise.process.transferdata import PullData
from powersimdata.scenario.state import State
from powersimdata.scenario.create import Create
from powersimdata.scenario.analyze import Analyze


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
            status = self._get_status(descriptor)
            if status == 0:
                return
            elif status == 1:
                self.state = Execute()
            elif status == 2:
                self.state = Analyze()

        print('State: <%s>' % self.state.name)
        self.state.init(self)


    def _get_status(self, descriptor):
        """Checks scenario status.

        :param str descriptor: scenario descriptor.
        :return: (*int*) -- scenario status.
        """
        td = PullData()
        table = td.get_scenario_table()
        table.set_index('id', inplace=True)

        def not_found_message(table, descriptor):
            """Print message when scenario is not found.

            :param pandas table: scenario table.
            :param str descriptor: scenario descriptor.
            """
            print('Scenario %s not found' % descriptor)
            print('Available scenarios are:')
            print(table[['name', 'interconnect', 'description']])

        try:
            id = int(descriptor)
            scenario = table[table.index == id]
            if scenario.shape[0] == 0:
                not_found_message(table, descriptor)
                return 0
            else:
                self.info = scenario
                return scenario.status.values[0]
        except:
            scenario = table[table.name == descriptor]
            if scenario.shape[0] == 0:
                not_found_message(table, descriptor)
                return 0
            elif scenario.shape[0] == 1:
                self.info = scenario
                return scenario.status.values[0]
            elif scenario.shape[0] > 1:
                print('Multiple scenarios with name "%s" found' % descriptor)
                print('Use index to access scenario')
                print(scenario[['name', 'interconnect', 'description']])
                return 0

    def change(self, state):
      """Changes state.

      :param class state: One of the sub-classes.
      """
      self.state.clean()
      self.state.switch(state)
      self.state.init(self)
