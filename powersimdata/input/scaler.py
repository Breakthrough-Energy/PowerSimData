from powersimdata.input.grid import Grid
from powersimdata.input.profiles import InputData

import copy

class Scaler(object):
    """Scales grid and input profiles using information stored in change \
        table.

    """

    def __init__(self, scenario_info, ssh_client):
        """Constructor.

        :param dict scenario_info: scenario information
        :param paramiko ssh_client: session with an SSH server.
        """
        self.scenario_id = scenario_info['id']
        self.interconnect = scenario_info['interconnect'].split('_')
        self._input = InputData(ssh_client)
        if scenario_info['change_table'] == 'Yes':
            self._load_ct()
        else:
            self.ct = {}
        self._load_grid()


    def _load_ct(self):
        """Loads change table.

        """
        try:
            self.ct = self._input.get_data(self.scenario_id, 'ct')
        except FileNotFoundError as e:
            raise(e)

    def _load_grid(self):
        """Loads original grid.

        """
        self._original_grid = Grid(self.interconnect)

    def get_grid(self):
        """Returns modified grid.

        :return: (*Grid*) -- instance of grid object.
        """
        self._grid = copy.deepcopy(self._original_grid)
        if bool(self.ct):
            for r in ['coal', 'ng', 'nuclear', 'hydro', 'solar', 'wind']:
                if r in list(self.ct.keys()):
                    try:
                        self.ct[r]['zone_id']
                        for key, value in self.ct[r]['zone_id'].items():
                            plant_id = self._grid.plant.groupby(
                                ['zone_id', 'type']).get_group(
                                (key, r)).index.values.tolist()
                            for i in plant_id:
                                self._grid.plant.loc[i, 'GenMWMax'] = \
                                    self._grid.plant.loc[i, 'GenMWMax'] * value
                                if r in ['coal', 'ng', 'nuclear']:
                                    self._grid.plant.loc[i, 'Pmax'] = \
                                        self._grid.plant.loc[i, 'Pmax'] * value
                    except:
                        pass
                    try:
                        self.ct[r]['plant_id']
                        for key, value in self.ct[r]['plant_id'].items():
                            self._grid.plant.loc[key, 'GenMWMax'] = \
                                self._grid.plant.loc[key, 'GenMWMax'] * value
                            if r in ['coal', 'ng', 'nuclear']:
                                self._grid.plant.loc[key, 'Pmax'] = \
                                    self._grid.plant.loc[key, 'Pmax'] * value
                    except:
                        pass
            if 'branch' in list(self.ct.keys()):
                try:
                    self.ct['branch']['zone_id']
                    for key, value in self.ct['branch']['zone_id'].items():
                        branch_id = self._grid.branch.groupby(
                            ['from_zone_id', 'to_zone_id']).get_group(
                            (key, key)).index.values.tolist()
                        for i in branch_id:
                            self._grid.branch.loc[i, 'rateA'] = \
                                self._grid.branch.loc[i, 'rateA'] * value
                except:
                    pass
                try:
                    self.ct['branch']['branch_id']
                    for key, value in self.ct['branch']['branch_id'].items():
                        self._grid.branch.loc[key, 'rateA'] = \
                            self._grid.branch.loc[key, 'rateA'] * value
                except:
                    pass
            if 'dcline' in list(self.ct.keys()):
                self.ct['dcline']['dcline_id']
                for key, value in self.ct['dcline']['dcline_id'].items():
                    if value == 0.0:
                        self._grid.dcline.loc[key, 'status'] = 0
                    else:
                        self._grid.dcline.loc[key, 'Pmax'] = \
                            self._grid.dcline.loc[key, 'Pmax'] * value


        return self._grid

    def get_power_output(self, resource):
        """Scales profile according to changes in change table and returns it.

        :param str resource: *'hydro'*, *'solar'* or *'wind'*.
        :return: (*pandas*) -- data frame of resource output with plant id \
            as columns and UTC timestamp as rows.
        :raises ValueError: if invalid resource.
        """
        possible = ['hydro', 'solar', 'wind']
        if resource not in possible:
            print("Choose one of:")
            for p in possible:
                print(p)
            raise ValueError('Invalid resource: %s' % resource)

        profile = self._input.get_data(self.scenario_id, resource)

        if bool(self.ct) and resource in list(self.ct.keys()):
            try:
                self.ct[resource]['zone_id']
                for key, value in self.ct[resource]['zone_id'].items():
                    plant_id = self._original_grid.plant.groupby(
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

    def get_hydro(self):
        """Returns scaled hydro profile.

        :return: (*pandas*) -- data frame of hydro.
        """
        return self.get_power_output('hydro')

    def get_solar(self):
        """Returns scaled solar profile.

        :return: (*pandas*) -- data frame of solar.
        """
        return self.get_power_output('solar')

    def get_wind(self):
        """Returns scaled wind profile.

        :return: (*pandas*) -- data frame of wind.
        """
        return self.get_power_output('wind')

    def get_demand(self):
        """Returns scaled demand profile.

        :return: (*pandas*) -- data frame of demand.
        """
        demand = self._input.get_data(self.scenario_id, 'demand')
        if bool(self.ct) and 'demand' in list(self.ct.keys()):
            for key, value in self.ct['demand']['zone_id'].items():
                zone_name = self._original_grid.zone[key]
                print('Multiply demand in %s (#%d) by %.2f' %
                      (self._original_grid.zone[key], key, value))
                demand.loc[:, key] *= value
        return demand
