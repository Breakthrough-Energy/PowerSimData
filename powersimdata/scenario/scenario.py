from postreise.process.transferdata import TransferData
from powersimdata.output.profiles import OutputData


class Scenario():
    """Retrieve information related a scenario

    :param str name: name of scenario.
    :param str data_dir: define local folder location to read or save data.
    """

    def __init__(self, name, data_dir=None):
        self.name = name
        self.data_dir = data_dir
        
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

    def get_pg(self):
        """Returns PG data frame.

        :return: (*pandas*) -- data frame of power generated.
        """

        od = OutputData(self.data_dir)
        pg = od.get_data(self.name, 'PG')

        return pg

    def get_pf(self):
        """Returns PF data frame.

        :return: (*pandas*) -- data frame of power flow.
        """

        od = OutputData(data_dir)
        pf = od.get_data(self.name, 'PF')

        return pf
