from powersimdata.input.scaler import Scaler
from powersimdata.output.profiles import OutputData
from powersimdata.scenario.state import State

import pandas as pd


class Analyze(State):
    """Scenario is in a state of being analyzed.

    """

    name = 'analyze'
    allowed = ['delete']

    def __init__(self, scenario):
        """Initializes attributes.

        """
        self._scenario_info = scenario._info
        print("SCENARIO: %s | %s \n" % (self._scenario_info['plan'],
                                        self._scenario_info['name']))
        self.scaler = Scaler(self._scenario_info['id'],
                             self._scenario_info['interconnect'].split('_'))

    def print_scenario_info(self):
        """Prints scenario information.

        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def _parse_infeasibilities(self):
        """Parses infeasibilities. When the optimizer cannot find a solution \
            in a time interval, the remedy is to decrease demand by some \
            amount until a solution is found. The purpose of this function is \
            to get the interval number(s) and the associated decrease(s).

        :return: (*dict*) -- keys are the interval number and the values are \
            the decrease in percent (%) applied to the original demand profile.
        """
        field = self._scenario_info['infeasibilities']
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
            dates = pd.date_range(start=self._scenario_info['start_date'],
                                  end=self._scenario_info['end_date'],
                                  freq=self._scenario_info['interval'])
            for key, value in infeasibilities.items():
                print("demand in %s - %s interval has been reduced by %d%%" %
                      (dates[key], dates[key+1], value))

    def get_PG(self):
        """Returns PG data frame.

        :return: (*pandas*) -- data frame of power generated.
        """
        od = OutputData()
        pg = od.get_data(self._scenario_info['id'], 'PG')

        return pg

    def get_PF(self):
        """Returns PF data frame.

        :return: (*pandas*) -- data frame of power flow.
        """
        od = OutputData()
        pf = od.get_data(self._scenario_info['id'], 'PF')

        return pf

    def get_ct(self):
        """Returns change table.

        :return: (*dict*) -- change table.
        """
        return self.scaler.ct

    def get_grid(self):
        """Returns Grid.

        :return: (*grid*) -- grid object
        """
        return self.scaler.get_grid()

    def get_demand(self, original=True):
        """Returns demand profiles.

        :param bool original: should the original demand profile or the \
            potentially modified one be returned.
        :return: (*pandas*) -- data frame of demand.
        """

        demand = self.scaler.get_demand()

        if original == True:
            return demand
        else:
            dates = pd.date_range(start=self._scenario_info['start_date'],
                                  end=self._scenario_info['end_date'],
                                  freq=self._scenario_info['interval'])
            infeasibilities = self._parse_infeasibilities()
            if infeasibilities is None:
                print("No infeasibilities. Return original profile.")
                return demand
            else:
                for key, value in infeasibilities.items():
                    demand[dates[key]:dates[key+1]] *= 1. - value / 100.
                return demand

    def get_hydro(self):
        """Returns hydro profile

        :return: (*pandas*) -- data frame of hydro power output.
        """
        return self.scaler.get_hydro()

    def get_solar(self):
        """Returns solar profile

        :return: (*pandas*) -- data frame of solar power output.
        """
        return self.scaler.get_solar()

    def get_wind(self):
        """Returns wind profile

        :return: (*pandas*) -- data frame of wind power output.
        """
        return self.scaler.get_wind()
