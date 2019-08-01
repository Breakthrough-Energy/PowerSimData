from powersimdata.input.grid import Grid
from powersimdata.input.profiles import InputData

import copy


class Scaler(object):
    """Scales grid and input profiles using information stored in change table.

    :param dict scenario_info: scenario information.
    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """
    
    _gen_types = [
        'coal', 'dfo', 'geothermal', 'ng', 'nuclear', 'hydro', 'solar', 'wind']
    _thermal_gen_types = ['coal', 'dfo', 'geothermal', 'ng', 'nuclear']

    def __init__(self, scenario_info, ssh_client):
        """Constructor.

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
        except FileNotFoundError:
            raise

    def _load_grid(self):
        """Loads original grid.

        """
        self._original_grid = Grid(self.interconnect)

    def get_grid(self):
        """Returns modified grid.

        :return: (*powersimdata.input.grid.Grid*) -- instance of grid object.
        """
        self._grid = copy.deepcopy(self._original_grid)
        if bool(self.ct):
            for r in self._gen_types:
                if r in list(self.ct.keys()):
                    try:
                        for key, value in self.ct[r]['zone_id'].items():
                            plant_id = self._grid.plant.groupby(
                                ['zone_id', 'type']).get_group(
                                (key, r)).index.values.tolist()
                            for i in plant_id:
                                self._grid.plant.loc[i, 'GenMWMax'] = \
                                    self._grid.plant.loc[i, 'GenMWMax'] * value
                                self._grid.plant.loc[i, 'Pmax'] = \
                                    self._grid.plant.loc[i, 'Pmax'] * value
                                self._grid.plant.loc[i, 'Pmin'] = \
                                    self._grid.plant.loc[i, 'Pmin'] * value
                                if r in self._thermal_gen_types:
                                    self._grid.gencost.loc[i, 'c0'] = \
                                        self._grid.gencost.loc[i, 'c0'] * value
                                    if value == 0:
                                        continue
                                    self._grid.gencost.loc[i, 'c2'] = \
                                        self._grid.gencost.loc[i, 'c2'] / value
                    except KeyError:
                        pass
                    try:
                        for key, value in self.ct[r]['plant_id'].items():
                            self._grid.plant.loc[key, 'GenMWMax'] = \
                                self._grid.plant.loc[key, 'GenMWMax'] * value
                            self._grid.plant.loc[key, 'Pmax'] = \
                                self._grid.plant.loc[key, 'Pmax'] * value
                            self._grid.plant.loc[key, 'Pmin'] = \
                                self._grid.plant.loc[key, 'Pmin'] * value
                            if r in self._thermal_gen_types:
                                self._grid.gencost.loc[key, 'c0'] = \
                                    self._grid.gencost.loc[key, 'c0'] * value
                                if value == 0:
                                    continue
                                self._grid.gencost.loc[key, 'c2'] = \
                                    self._grid.gencost.loc[key, 'c2'] / value
                    except KeyError:
                        pass
            if 'branch' in list(self.ct.keys()):
                try:
                    for key, value in self.ct['branch']['zone_id'].items():
                        branch_id = self._grid.branch.groupby(
                            ['from_zone_id', 'to_zone_id']).get_group(
                            (key, key)).index.values.tolist()
                        for i in branch_id:
                            self._grid.branch.loc[i, 'rateA'] = \
                                self._grid.branch.loc[i, 'rateA'] * value
                            self._grid.branch.loc[i, 'x'] = \
                                self._grid.branch.loc[i, 'x'] / value
                except KeyError:
                    pass
                try:
                    for key, value in self.ct['branch']['branch_id'].items():
                        self._grid.branch.loc[key, 'rateA'] = \
                            self._grid.branch.loc[key, 'rateA'] * value
                        self._grid.branch.loc[key, 'x'] = \
                            self._grid.branch.loc[key, 'x'] / value
                except KeyError:
                    pass
            if 'dcline' in list(self.ct.keys()):
                for key, value in self.ct['dcline']['dcline_id'].items():
                    if value == 0.0:
                        self._grid.dcline.loc[key, 'status'] = 0
                    else:
                        self._grid.dcline.loc[key, 'Pmin'] = \
                            self._grid.dcline.loc[key, 'Pmin'] * value
                        self._grid.dcline.loc[key, 'Pmax'] = \
                            self._grid.dcline.loc[key, 'Pmax'] * value
            if 'storage' in list(self.ct.keys()):
                storage = copy.deepcopy(self._grid.storage)
                storage_id = self._grid.plant.shape[0]
                for key, value in self.ct['storage']['bus_id'].items():
                    # need new index for this new generator
                    storage_id += 1

                    # build and append new row of gen
                    gen = {g: 0
                           for g in self._grid.storage['gen'].columns}
                    gen['bus_id'] = key
                    gen['Vg'] = 1
                    gen['mBase'] = 100
                    gen['status'] = 1
                    gen['Pmax'] = value
                    gen['Pmin'] = -1 * value
                    gen['ramp_10'] = value
                    gen['ramp_30'] = value
                    storage['gen'] = storage['gen'].append(
                        gen, ignore_index=True)

                    # build and append new row of gencost
                    gencost = {g: 0
                               for g in self._grid.storage['gencost'].columns}
                    gencost['type'] = 2
                    gencost['n'] = 3
                    storage['gencost'] = storage['gencost'].append(
                        gencost, ignore_index=True)

                    # build and append new row of genfuel
                    storage['genfuel'].append('ess')

                    # build and append new row of StorageData.
                    data = {g: 0
                            for g in self._grid.storage['StorageData'].columns}
                    data['UnitIdx'] = storage_id
                    data['ExpectedTerminalStorageMax'] = \
                        value * storage['duration'] * storage['max_stor']
                    data['ExpectedTerminalStorageMin'] = \
                        value * storage['duration'] / 2
                    data['InitialStorage'] = value * storage['duration'] / 2
                    data['InitialStorageLowerBound'] = \
                        value * storage['duration'] / 2
                    data['InitialStorageUpperBound'] = \
                        value * storage['duration'] / 2
                    data['InitialStorageCost'] = storage['energy_price']
                    data['TerminalStoragePrice'] = storage['energy_price']
                    data['MinStorageLevel'] = \
                        value * storage['duration'] * storage['min_stor']
                    data['MinStorageLevel'] = \
                        value * storage['duration'] * storage['max_stor']
                    data['OutEff'] = storage['OutEff']
                    data['InEff'] = storage['InEff']
                    data['LossFactor'] = 0
                    data['rho'] = 1
                    storage['StorageData'] = storage['StorageData'].append(
                        data, ignore_index=True)
            else:
                storage = []
            self._grid.storage = storage

        return self._grid

    def get_power_output(self, resource):
        """Scales profile according to changes enclosed in change table.

        :param str resource: *'hydro'*, *'solar'* or *'wind'*.
        :return: (*pandas.DataFrame*) -- data frame of resource output with
            plant id as columns and UTC timestamp as rows.
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
                for key, value in self.ct[resource]['zone_id'].items():
                    plant_id = self._original_grid.plant.groupby(
                        ['zone_id', 'type']).get_group(
                        (key, resource)).index.values.tolist()
                    for i in plant_id:
                        profile.loc[:, i] *= value
            except KeyError:
                pass
            try:
                for key, value in self.ct[resource]['plant_id'].items():
                    profile.loc[:, key] *= value
            except KeyError:
                pass

        return profile

    def get_hydro(self):
        """Returns scaled hydro profile.

        :return: (*pandas.DataFrame*) -- data frame of hydro.
        """
        return self.get_power_output('hydro')

    def get_solar(self):
        """Returns scaled solar profile.

        :return: (*pandas.DataFrame*) -- data frame of solar.
        """
        return self.get_power_output('solar')

    def get_wind(self):
        """Returns scaled wind profile.

        :return: (*pandas.DataFrame*) -- data frame of wind.
        """
        return self.get_power_output('wind')

    def get_demand(self):
        """Returns scaled demand profile.

        :return: (*pandas.DataFrame*) -- data frame of demand.
        """
        demand = self._input.get_data(self.scenario_id, 'demand')
        if bool(self.ct) and 'demand' in list(self.ct.keys()):
            for key, value in self.ct['demand']['zone_id'].items():
                print('Multiply demand in %s (#%d) by %.2f' %
                      (self._original_grid.id2zone[key], key, value))
                demand.loc[:, key] *= value
        return demand
