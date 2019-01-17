from postreise.process.transferdata import TransferData

class Scenario():
    """Retrieve information related a scenario

    :param str name: name of scenario.

    """

    def __init__(self, name):
        self.name = name
        
        # Check scenario
        self._check_scenario()

    def _check_scenario(self):
        td = TransferData()
        scenarios = td.get_scenario_list()
        if self.name not in scenarios:
            print("Scenario not available. Possible scenarios are:")
            for s in scenarios:
                print(s)
            return

        
