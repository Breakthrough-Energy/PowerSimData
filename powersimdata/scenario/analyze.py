from math import radians, cos, sin, asin, sqrt

import pandas as pd

from powersimdata.input.scaler import Scaler
from powersimdata.output.profiles import OutputData
from powersimdata.scenario.state import State

def _haversine(point1, point2):
    """Given two lat/long pairs, return distance in miles.
    
    :param tuple (number, number) point1: first point, (lat, long) in degrees.
    :param tuple (number, number) point2: second point, (lat, long) in degrees.
    
    :return: distance in miles, float
    
    """
    
    _AVG_EARTH_RADIUS_MILES = 3958.7613
    
    # unpack latitude/longitude
    lat1, lng1 = point1
    lat2, lng2 = point2
    
    # convert all latitudes/longitudes from decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    
    # calculate haversine
    lat = lat2 - lat1
    lng = lng2 - lng1
    d = 2 * _AVG_EARTH_RADIUS_MILES * asin(sqrt(
        sin(lat * 0.5) ** 2 + cos(lat1) * cos(lat2) * sin(lng * 0.5) ** 2))
    
    return d

def _calculate_mw_miles(original_grid, ct):
    """Given a change table, calculate the number of upgraded lines and 
    transformers, and the total upgrade quantity (in MW and MW-miles).
    Currently only supports change_tables that specify branches, not zone_name.
    Currently lumps Transformer and TransformerWinding upgrades together.
    
    :param powersimdata.input.grid original_grid: grid instance.
    :param powersimdata.input.change_table ct: change_table instance.
    
    :return: a dict of keys (types of upgrades) and values (floats/ints).
    """
    
    upgrade_categories = (
        'mw_miles', 'transformer_mw','num_lines', 'num_transformers')
    upgrades = {u: 0 for u in upgrade_categories}
    
    base_branch = original_grid.branch
    upgraded_branches = ct['branch']['branch_id']
    for b, v in upgraded_branches.items():
        # 'upgraded' capacity is v-1 because a scale of 1 = an upgrade of 0
        upgraded_capacity = base_branch.loc[b,'rateA'] * (v-1)
        device_type = base_branch.loc[b,'branch_device_type']
        if device_type == 'Line':
            from_coords = (
                base_branch.loc[b,'from_lat'], base_branch.loc[b,'from_lon'])
            to_coords = (
                base_branch.loc[b,'to_lat'], base_branch.loc[b,'to_lon'])
            addtl_mw_miles = (
                upgraded_capacity * _haversine(from_coords, to_coords))
            upgrades['mw_miles'] += addtl_mw_miles
            upgrades['num_lines'] += 1
        elif device_type == 'Transformer':
            upgrades['transformer_mw'] += upgraded_capacity
            upgrades['num_transformers'] += 1
        elif device_type == 'TransformerWinding':
            upgrades['transformer_mw'] += upgraded_capacity
            upgrades['num_transformers'] += 1
        else:
            raise Exception('Unknown branch: ' + str(b))
    
    return upgrades

class Analyze(State):
    """Scenario is in a state of being analyzed.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = 'analyze'
    allowed = ['delete']

    def __init__(self, scenario):
        """Constructor.

        """
        self._scenario_info = scenario.info
        self._ssh = scenario.ssh

        print("SCENARIO: %s | %s\n" % (self._scenario_info['plan'],
                                       self._scenario_info['name']))
        print("--> State\n%s" % self.name)
        self.scaler = Scaler(self._scenario_info, self._ssh)

    def print_scenario_info(self):
        """Prints scenario information.

        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def _parse_infeasibilities(self):
        """Parses infeasibilities. When the optimizer cannot find a solution in
            a time interval, the remedy is to decrease demand by some amount
            until a solution is found. The purpose of this function is to get
            the interval number(s) and the associated decrease(s).

        :return: (*dict*) -- keys are the interval number and the values are
            the decrease in percent (%) applied to the original demand profile.
        """
        field = self._scenario_info['infeasibilities']
        if field == '':
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
                      (dates[key],
                       dates[key]+pd.Timedelta(self._scenario_info['interval']),
                       value))

    def calculate_mw_miles(self):
        mw_miles = _calculate_mw_miles(
            original_grid=self.scaler._original_grid,
            ct=self.ct)
    
    def get_pg(self):
        """Returns PG data frame.

        :return: (*pandas.DataFrame*) -- data frame of power generated.
        """
        od = OutputData(self._ssh)
        pg = od.get_data(self._scenario_info['id'], 'PG')

        return pg

    def get_pf(self):
        """Returns PF data frame.

        :return: (*pandas.DataFrame*) -- data frame of power flow.
        """
        od = OutputData(self._ssh)
        pf = od.get_data(self._scenario_info['id'], 'PF')

        return pf

    def get_dcline_pf(self):
        """Returns PF_DCLINE data frame.

        :return: (*pandas.DataFrame*) -- data frame of power flow on DC line(s).
        """
        od = OutputData(self._ssh)
        dcline_pf = od.get_data(self._scenario_info['id'], 'PF_DCLINE')

        return dcline_pf

    def get_lmp(self):
        """Returns LMP data frame. LMP = locational marginal price

        :return: (*pandas.DataFrame*) -- data frame of nodal prices.
        """
        od = OutputData(self._ssh)
        lmp = od.get_data(self._scenario_info['id'], 'LMP')

        return lmp
    
    def get_congu(self):
        """Returns CONGU data frame. CONGU = Congestion, Upper flow limit

        :return: (*pandas.DataFrame*) -- data frame of branch flow mu (upper).
        """
        od = OutputData(self._ssh)
        congu = od.get_data(self._scenario_info['id'], 'CONGU')

        return congu
    
    def get_congl(self):
        """Returns CONGL data frame. CONGL = Congestion, Lower flow limit

        :return: (*pandas.DataFrame*) -- data frame of branch flow mu (lower).
        """
        od = OutputData(self._ssh)
        congl = od.get_data(self._scenario_info['id'], 'CONGL')

        return congl

    def get_storage_pg(self):
        """Returns STORAGE_PG data frame.

        :return: (*pandas.DataFrame*) -- data frame of power generated by
            storage units.
        """
        od = OutputData(self._ssh)
        storage_pg = od.get_data(self._scenario_info['id'], 'STORAGE_PG')

        return storage_pg

    def get_storage_e(self):
        """Returns STORAGE_E data frame. Energy state of charge.

        :return: (*pandas.DataFrame*) -- data frame of energy state of charge.
        """
        od = OutputData(self._ssh)
        storage_e = od.get_data(self._scenario_info['id'], 'STORAGE_E')

        return storage_e

    def get_ct(self):
        """Returns change table.

        :return: (*dict*) -- change table.
        """
        return self.scaler.ct

    def get_grid(self):
        """Returns Grid.

        :return: (*powersimdata.input.grid.Grid*) -- instance of grid object.
        """
        return self.scaler.get_grid()

    def get_demand(self, original=True):
        """Returns demand profiles.

        :param bool original: should the original demand profile or the
            potentially modified one be returned.
        :return: (*pandas.DataFrame*) -- data frame of demand.
        """

        demand = self.scaler.get_demand()

        if original:
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
                    start = dates[key]
                    end = dates[key] + \
                          pd.Timedelta(self._scenario_info['interval']) - \
                          pd.Timedelta('1H')
                    demand[start:end] *= 1. - value / 100.
                return demand

    def get_hydro(self):
        """Returns hydro profile

        :return: (*pandas.DataFrame*) -- data frame of hydro power output.
        """
        return self.scaler.get_hydro()

    def get_solar(self):
        """Returns solar profile

        :return: (*pandas.DataFrame*) -- data frame of solar power output.
        """
        return self.scaler.get_solar()

    def get_wind(self):
        """Returns wind profile

        :return: (*pandas.DataFrame*) -- data frame of wind power output.
        """
        return self.scaler.get_wind()
