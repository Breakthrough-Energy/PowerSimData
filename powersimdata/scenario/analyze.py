from powersimdata.input.grid import Grid
from powersimdata.input.profiles import InputData
from powersimdata.output.profiles import OutputData
from powersimdata.scenario.state import State

import pandas as pd


class Analyze(State):
    """Scenario is in a state of being analyzed.

    """

    name = 'analyze'
    allowed = ['delete', 'modify']

    def __init__(self, scenario):
        """Initializes attributes.

        """
        self.scenario_info = scenario.info
        self._get_ct()
        self._get_grid()

    def _get_ct(self):
        """Loads change table.

        """
        id = InputData()
        try:
            print('# Change table')
            ct = id.get_data(str(self.scenario_info['id']), 'ct')
            self.ct = ct
        except:
            print("No change table for scenario #%d" %
                  self.scenario_info['id'])
            self.ct = None

    def _get_grid(self):
        """Loads original grid and apply changes found in change table.

        """
        print('# Grid')
        interconnect = self.scenario_info['interconnect'].split('_')
        self.grid = Grid(interconnect)
        if self.ct is not None:
            for r in ['hydro', 'solar', 'wind']:
                if r in list(self.ct.keys()):
                    try:
                        self.ct[r]['zone_id']
                        for key, value in self.ct[r]['zone_id'].items():
                            plant_id = self.grid.plant.groupby(
                                ['zone_id', 'type']).get_group(
                                (key, r)).index.values.tolist()
                            for i in plant_id:
                                self.grid.plant.loc[i, 'GenMWMax'] = \
                                    self.grid.plant.loc[i, 'GenMWMax'] * value
                    except:
                        pass
                    try:
                        self.ct[r]['plant_id']
                        for key, value in self.ct[r]['plant_id'].items():
                            self.grid.plant.loc[key, 'GenMWMax'] = \
                                self.grid.plant.loc[key, 'GenMWMax'] * value
                    except:
                        pass
            if 'branch' in list(self.ct.keys()):
                try:
                    self.ct['branch']['zone_id']
                    for key, value in self.ct['branch']['zone_id'].items():
                        branch_id = self.grid.branch.groupby(
                                ['from_zone_id', 'to_zone_id']).get_group(
                                (key, key)).index.values.tolist()
                        for i in branch_id:
                            self.grid.branch.loc[i, 'rateA'] = \
                                self.grid.branch.loc[i, 'rateA'] * value
                except:
                    pass
                try:
                    self.ct['branch']['branch_id']
                    for key, value in self.ct['branch']['branch_id'].items():
                        self.grid.branch.loc[key, 'rateA'] = \
                            self.grid.branch.loc[key, 'rateA'] * value
                except:
                    pass

    def _get_power_output(self, resource):
        """Scales profile according to changes in change table and returns it.

        :param str resource: *'hydro'*, *'solar'* or *'wind'*.
        :return: (*pandas*) -- data frame of resource output with plant id \
            as columns and UTC timestamp as rows.
        :raises NameError: if invalid resource.
        """
        possible = ['branch', 'hydro', 'solar', 'wind']
        if resource not in possible:
            print("Choose one of:")
            for p in possible:
                print(p)
            raise NameError('Invalid resource')

        id = InputData()
        profile = id.get_data(str(self.scenario_info['id']), resource)

        if self.ct is not None and resource in list(self.ct.keys()):
            try:
                self.ct[resource]['zone_id']
                for key, value in self.ct[resource]['zone_id'].items():
                    plant_id = self.grid.plant.groupby(
                        ['zone_id', 'type']).get_group(
                        (key, resource)).index.values.tolist()
                    for i in plant_id:
                        profile.loc[:, i] *= value
            except:
                pass
            try:
                self.ct[resource]['plant_id']
                for key, value in self.ct[resource]['plant_id'].items():
                    profile.loc[:, key] *= value
            except:
                pass

        return profile

    def _parse_infeasibilities(self):
        """Parses infeasibilities. When the optimizer cannot find a solution \
            in a time interval, the remedy is to decrease demand by some \
            amount until a solution is found. The purpose of this function is \
            to get the interval number(s) and the associated decrease(s).

        :return: (*dict*) -- keys are the interval number and the values are \
            the decrease in percent (%) applied to the original demand profile.
        """
        field = self.scenario_info['infeasibilities']
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
            dates = pd.date_range(start=self.scenario_info['start_date'],
                                  end=self.scenario_info['end_date'],
                                  freq=self.scenario_info['interval'])
            for key, value in infeasibilities.items():
                print("demand in %s - %s interval has been reduced by %d%%" %
                      (dates[key], dates[key+1], value))

    def get_PG(self):
        """Returns PG data frame.

        :return: (*pandas*) -- data frame of power generated.
        """
        od = OutputData()
        pg = od.get_data(str(self.scenario_info['id']), 'PG')

        return pg

    def get_PF(self):
        """Returns PF data frame.

        :return: (*pandas*) -- data frame of power flow.
        """
        od = OutputData()
        pf = od.get_data(str(self.scenario_info['id']), 'PF')

        return pf

    def get_demand(self, original=True):
        """Returns demand profiles.

        :param bool original: should the original demand profile or the \
            potentially modified one be returned.
        :return: (*pandas*) -- data frame of demand.
        """

        id = InputData()
        demand = id.get_data(str(self.scenario_info['id']), 'demand')
        if self.ct is not None and 'demand' in list(self.ct.keys()):
            for key, value in self.ct['demand']['zone_id'].items():
                zone_name = self.grid.zone[key]
                print('Multiply demand in %s (#%d) by %.2f' %
                      (self.grid.zone[key], key, value))
                demand.loc[:, key] *= value

        if original == True:
            return demand
        else:
            dates = pd.date_range(start=self.scenario_info['start_date'],
                                  end=self.scenario_info['end_date'],
                                  freq=self.scenario_info['interval'])
            infeasibilities = self._parse_infeasibilities()
            if infeasibilities is None:
                print("There are no infeasibilities. Return original profile.")
                return demand
            else:
                for key, value in infeasibilities.items():
                    demand[dates[key]:dates[key+1]] *= 1. - value / 100.
                return demand

    def get_hydro(self):
        """Returns hydro profile

        """
        return self._get_power_output('hydro')

    def get_solar(self):
        """Returns solar profile

        """
        return self._get_power_output('solar')

    def get_wind(self):
        """Returns wind profile

        """
        return self._get_power_output('wind')
