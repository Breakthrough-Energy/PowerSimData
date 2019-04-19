from powersimdata.input.grid import Grid
from powersimdata.scenario.state import State
from postreise.process.transferdata import PullData

from collections import OrderedDict


class Execute(State):
    """Scenario is in a state of being executed.

    """
    name = 'execute'
    allowed = ['stop']

    def __init__(self, scenario):
        """Initializes attributes.

        :param class scenario: scenario instance.
        """
        self._scenario_info = scenario._info
        self._scenario_status = scenario._status
        print("SCENARIO: %s | %s\n" % (self._scenario_info['plan'],
                                     self._scenario_info['name']))
        print("# Status\n--> %s" % self._scenario_status)

    def get_status(self):
        td = PullData()
        table = td.get_execute_table()

        status = table[table.id == self._scenario_info['id']].status[0]
        return status

    def print_scenario_info(self):
        """Prints scenario information.

        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))
