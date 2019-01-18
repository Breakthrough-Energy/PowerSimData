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
        
        # Communicate with server
        td = TransferData()
        
        # Check that scenario
        self._check_name(td.get_scenario_list())
        
        # Retrieve information on scenario
        self._retrieve_info(td.get_scenario_table())
        

    def _check_name(self, names):
        """Checks if scenario exists.

        :param list: list of scenario names.
        """
        if self.name not in names:
            print("Scenario not available. Possible scenarios are:")
            for n in names:
                print(n)
            return

    def _retrieve_info(self, table):
        """Retrieve scenario information.
        
        """
        self.info = table[table['name'] == self.name]
        
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
        od = OutputData(self.data_dir)
        pf = od.get_data(self.name, 'PF')

        return pf
