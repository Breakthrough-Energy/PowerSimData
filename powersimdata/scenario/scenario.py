from postreise.process.transferdata import PullData
from powersimdata.scenario.analyze import Analyze
from powersimdata.scenario.create import Create
from powersimdata.scenario.execute import Execute

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
            self.state = Create(self)
        else:
            status = self._get_status(descriptor)
            if status == 0:
                return
            elif status == 1:
                self.state = Execute(self)
            elif status == 2:
                self.state = Analyze(self)

    def _get_status(self, descriptor):
        """Checks scenario status.

        :param str descriptor: scenario descriptor.
        :return: (*int*) -- scenario status.
        """
        td = PullData()
        table = td.get_scenario_table()

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
            scenario = table[table.id == id]
            if scenario.shape[0] == 0:
                not_found_message(table, descriptor)
                return 0
            else:
                self.info = scenario.to_dict('records')[0]
                return self.info['status']
        except:
            scenario = table[table.name == descriptor]
            if scenario.shape[0] == 0:
                not_found_message(table, descriptor)
                return 0
            elif scenario.shape[0] == 1:
                self.info = scenario.to_dict('records')[0]
                return self.info['status']
            elif scenario.shape[0] > 1:
                print('Multiple scenarios with name "%s" found' % descriptor)
                print('Use index to access scenario')
                print(scenario[['name', 'interconnect', 'description']])
                return 0

    def change(self, state):
      """Changes state.

      :param class state: One of the sub-classes.
      """
      self.state.switch(state)
