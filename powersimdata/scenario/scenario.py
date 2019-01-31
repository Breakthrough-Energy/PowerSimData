import pandas as pd

from postreise.process.transferdata import PullData
from powersimdata.input.profiles import InputData
from powersimdata.output.profiles import OutputData


class Scenario():
    """Retrieve information related a scenario

    :param str name: name of scenario.
    :param str data_dir: define local folder location to read or save data.

    """

    def __init__(self, name, data_dir=None):
        """Constructor.

        """
        self.data_dir = data_dir

        # Check/set scenario name
        self._check_name(name)

        # Retrieve scenario information
        self._retrieve_info()


    def _check_name(self, name):
        """Checks if scenario exists.

        :param list name: scenario name.
        :raises NameError: if scenario does not exist.
        """
        td = PullData()
        possible = td.get_scenario_list()
        if name not in possible:
            raise NameError("Scenario not available. Choose among %s" %
                            " / ".join(possible))
        self.name = name

    def _retrieve_info(self):
        """Retrieve scenario information.

        """
        td = PullData()
        table = td.get_scenario_table()
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

    def _parse_infeasibilities(self):
        """Parses infeasibilities. When the optimizer cannot find a solution \
            in a time interval, the remedy is to decrease demand by some \
            amount until a solution is found. The purpose of this function is \
            to get the interval number and the associated decrease.

        :return: (*dict*) -- keys are the interval number and the values are \
            the decrease in percent (%) applied to the original demand \
            profile.
        """
        field = self.info.infeasibilities[0]
        if field == 'No':
            return None
        else:
            infeasibilities = {}
            for entry in field.split('_'):
                item = entry.split(':')
                infeasibilities[int(item[0])] = int(item[1])
            return infeasibilities

    def print_infeasibilities(self):
        """Prints infeasibilities.

        """
        infeasibilities = self._parse_infeasibilities()
        if infeasibilities is None:
            print("There are no infeasibilities.")
        else:
            dates = pd.date_range(start=self.info.start_date[0],
                                  end=self.info.end_date[0],
                                  freq=self.info.interval[0])
            for key, value in infeasibilities.items():
                print("demand in %s - %s interval has been reduced by %d%%" %
                      (dates[key], dates[key+1], value))


    def get_demand(self, original=True):
        """Returns demand profiles.

        :param bool original: should the original demand profile or the \
            potentially modified one be returned.
        :return: (*pandas*) -- data frame of demand.
        """

        id = InputData(self.data_dir)
        demand = id.get_data(self.name, 'demand')
        if original == True:
            return demand
        else:
            dates = pd.date_range(start=self.info.start_date[0],
                                  end=self.info.end_date[0],
                                  freq=self.info.interval[0])
            infeasibilities = self._parse_infeasibilities()
            if infeasibilities is None:
                print("There are no infeasibilities. Return original profile.")
                return demand
            else:
                for key, value in infeasibilities.items():
                    demand[dates[key]:dates[key+1]] *= 1. - value / 100.
                return demand
