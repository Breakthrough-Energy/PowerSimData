from powersimdata.input.grid import Grid
from powersimdata.scenario.state import State


class Execute(State):
    """Scenario is in a state of being executed.

    """
    name = 'execute'
    allowed = ['delete']

    def __init__(self, scenario):
        """Initializes attributes.

        """
        self._scenario_info = scenario._info
        print("SCENARIO: %s | %s" % (self._scenario_info['plan'],
                                     self._scenario_info['name']))

    def print_scenario_info(self):
        """Prints scenario information.

        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))
