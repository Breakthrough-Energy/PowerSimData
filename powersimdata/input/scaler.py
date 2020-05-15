import copy
import numpy as np
import pandas as pd

from powersimdata.input.grid import Grid
from powersimdata.input.profiles import InputData
from powersimdata.input.helpers import PrintManager
from powersimdata.utility.distance import haversine


class TransformGrid(object):
    """Transforms grid according to operations listed in change table.

    """

    def __init__(self, grid, ct):
        """Constructor

        :param powersimdata.input.grid.Grid grid: a Grid object.
        :param dict ct: change table
        """
        self.grid = copy.deepcopy(grid)
        self.ct = ct
        self.gen_types = ['biomass', 'coal', 'dfo', 'geothermal', 'ng',
                          'nuclear', 'hydro', 'solar', 'wind', 'wind_offshore',
                          'other']
        self.thermal_gen_types = ['coal', 'dfo', 'geothermal', 'ng', 'nuclear']

    def get_grid(self):
        """Returns the transformed grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        if bool(self.ct):
            self._apply_change_table()
        return self.grid

    def _apply_change_table(self):
        """Apply changes listed in change table to the grid.

        """
        for g in self.gen_types:
            if g in self.ct.keys():
                self._scale_gen(g)

        if 'branch' in self.ct.keys():
            self._scale_branch()

        if 'dcline' in self.ct.keys():
            self._scale_dcline()

        if 'new_branch' in self.ct.keys():
            self._add_branch()

        if 'new_dcline' in self.ct.keys():
            self._add_dcline()

        if 'storage' in self.ct.keys():
            self._add_storage()

    def _scale_gen(self, gen_type):
        """Scales capacity of generators and the associated generation cost.

        :param str gen_type: type of generator.
        """
        if 'zone_id' in self.ct[gen_type].keys():
            for zone_id, factor in self.ct[gen_type]['zone_id'].items():
                plant_id = self.grid.plant.groupby(
                    ['zone_id', 'type']).get_group(
                    (zone_id, gen_type)).index.values.tolist()
                self._scale_gen_capacity(plant_id, factor)
                if gen_type in self.thermal_gen_types:
                    self._scale_gencost(plant_id, factor)
        if 'plant_id' in self.ct[gen_type].keys():
            for plant_id, factor in self.ct[gen_type]['plant_id'].items():
                self._scale_gen_capacity(plant_id, factor)
                if gen_type in self.thermal_gen_types:
                    self._scale_gencost(plant_id, factor)

    def _scale_gen_capacity(self, plant_id, factor):
        """Scales capacity of plants.

        :param int/list plant_id: plant identification number(s).
        :param float factor: scaling factor.
        """
        self.grid.plant.loc[plant_id, 'Pmax'] *= factor
        self.grid.plant.loc[plant_id, 'Pmin'] *= factor

    def _scale_gencost(self, plant_id, factor):
        """Scales generation cost curves.

        :param int/list plant_id: plant identification number(s).
        :param float factor: scaling factor.
        :return:
        """
        self.grid.gencost['before'].loc[plant_id, 'c0'] *= factor
        if factor != 0:
            self.grid.gencost['before'].loc[plant_id, 'c2'] /= factor

    def _scale_branch(self):
        """Scales capacity of AC lines.

        """
        if 'zone_id' in self.ct['branch'].keys():
            for zone_id, factor in self.ct['branch']['zone_id'].items():
                branch_id = self.grid.branch.groupby(
                    ['from_zone_id', 'to_zone_id']).get_group(
                    (zone_id, zone_id)).index.values.tolist()
                self._scale_branch_capacity(branch_id, factor)
        if 'branch_id' in self.ct['branch'].keys():
            for branch_id, factor in self.ct['branch']['branch_id'].items():
                self._scale_branch_capacity(branch_id, factor)

    def _scale_branch_capacity(self, branch_id, factor):
        """Scales capacity of AC lines.

        :param int/list branch_id: branch identification number(s)
        :param float factor: scaling factor
        """
        self.grid.branch.loc[branch_id, 'rateA'] *= factor
        self.grid.branch.loc[branch_id, 'x'] /= factor

    def _scale_dcline(self):
        """Scales capacity of HVDC lines.

        """
        for dcline_id, factor in self.ct['dcline']['dcline_id'].items():
            if factor == 0:
                self.grid.dcline.loc[dcline_id, 'status'] = 0
            else:
                self.grid.dcline.loc[dcline_id, 'Pmin'] *= factor
                self.grid.dcline.loc[dcline_id, 'Pmax'] *= factor

    def _add_branch(self):
        """Adds branch(es) to the grid.

        """
        new_branch = {c: 0 for c in self.grid.branch.columns}
        v2x = voltage_to_x_per_distance(self.grid)
        for entry in self.ct['new_branch']:
            from_bus_id = entry['from_bus_id']
            to_bus_id = entry['to_bus_id']
            interconnect = self.grid.bus.loc[from_bus_id].interconnect
            from_zone_id = self.grid.bus.loc[from_bus_id].zone_id
            to_zone_id = self.grid.bus.loc[to_bus_id].zone_id
            from_zone_name = self.grid.id2zone[from_zone_id]
            to_zone_name = self.grid.id2zone[to_zone_id]
            from_lon = self.grid.bus.loc[from_bus_id].lon
            from_lat = self.grid.bus.loc[from_bus_id].lat
            to_lon = self.grid.bus.loc[to_bus_id].lon
            to_lat = self.grid.bus.loc[to_bus_id].lat
            from_basekv = v2x[self.grid.bus.loc[from_bus_id].baseKV]
            to_basekv = v2x[self.grid.bus.loc[to_bus_id].baseKV]
            distance = haversine((from_lat, from_lon), (to_lat, to_lon))
            x = distance * np.mean([from_basekv, to_basekv])

            new_branch['from_bus_id'] = entry['from_bus_id']
            new_branch['to_bus_id'] = entry['to_bus_id']
            new_branch['status'] = 1
            new_branch['ratio'] = 0
            new_branch['branch_device_type'] = 'Line'
            new_branch['rateA'] = entry['capacity']
            new_branch['interconnect'] = interconnect
            new_branch['from_zone_id'] = from_zone_id
            new_branch['to_zone_id'] = to_zone_id
            new_branch['from_zone_name'] = from_zone_name
            new_branch['to_zone_name'] = to_zone_name
            new_branch['from_lon'] = from_lon
            new_branch['from_lat'] = from_lat
            new_branch['to_lon'] = to_lon
            new_branch['to_lat'] = to_lat
            new_branch['x'] = x
            self.grid.branch = self.grid.branch.append(new_branch,
                                                       ignore_index=True)

    def _add_dcline(self):
        """Adds HVDC line(s) to the grid

        """
        new_dcline = {c: 0 for c in self.grid.dcline.columns}
        for entry in self.ct['new_dcline']:
            from_bus_id = entry['from_bus_id']
            to_bus_id = entry['to_bus_id']
            from_interconnect = self.grid.bus.loc[from_bus_id].interconnect
            to_interconnect = self.grid.bus.loc[to_bus_id].interconnect
            new_dcline['from_bus_id'] = entry['from_bus_id']
            new_dcline['to_bus_id'] = entry['to_bus_id']
            new_dcline['status'] = 1
            new_dcline['Pf'] = entry['capacity']
            new_dcline['Pt'] = 0.98 * entry['capacity']
            new_dcline['Pmin'] = -1 * entry['capacity']
            new_dcline['Pmax'] = entry['capacity']
            new_dcline['from_interconnect'] = from_interconnect
            new_dcline['to_interconnect'] = to_interconnect
            self.grid.dcline = self.grid.dcline.append(new_dcline,
                                                       ignore_index=True)

    def _add_storage(self):
        """Adds storage to the grid.

        """
        storage_id = self.grid.plant.shape[0]
        for bus_id, value in self.ct['storage']['bus_id'].items():
            storage_id += 1
            self._add_storage_unit(bus_id, value)
            self._add_storage_gencost()
            self._add_storage_genfuel()
            self._add_storage_data(storage_id, value)

    def _add_storage_unit(self, bus_id, value):
        """Add storage unit.

        :param int bus_id: bus identification number.
        :param float value: storage capacity.
        """
        gen = {g: 0 for g in self.grid.storage['gen'].columns}
        gen['bus_id'] = bus_id
        gen['Vg'] = 1
        gen['mBase'] = 100
        gen['status'] = 1
        gen['Pmax'] = value
        gen['Pmin'] = -1 * value
        gen['ramp_10'] = value
        gen['ramp_30'] = value
        self.grid.storage['gen'] = \
            self.grid.storage['gen'].append(gen, ignore_index=True)

    def _add_storage_gencost(self):
        """Sets generation cost of storage unit.

        """
        gencost = {g: 0 for g in self.grid.storage['gencost'].columns}
        gencost['type'] = 2
        gencost['n'] = 3
        self.grid.storage['gencost'] = \
            self.grid.storage['gencost'].append(gencost, ignore_index=True)

    def _add_storage_genfuel(self):
        """Sets fuel type of storage unit.

        """
        self.grid.storage['genfuel'].append('ess')

    def _add_storage_data(self, storage_id, value):
        """Sets storage data.

        :param int storage_id: storage identification number.
        :param float value: storage capacity.
        """
        data = {g: 0 for g in self.grid.storage['StorageData'].columns}

        duration = self.grid.storage['duration']
        min_stor = self.grid.storage['min_stor']
        max_stor = self.grid.storage['max_stor']
        energy_price = self.grid.storage['energy_price']

        data['UnitIdx'] = storage_id
        data['ExpectedTerminalStorageMax'] = value * duration * max_stor
        data['ExpectedTerminalStorageMin'] = value * duration / 2
        data['InitialStorage'] = value * duration / 2
        data['InitialStorageLowerBound'] = value * duration / 2
        data['InitialStorageUpperBound'] = value * duration / 2
        data['InitialStorageCost'] = energy_price
        data['TerminalStoragePrice'] = energy_price
        data['MinStorageLevel'] = value * duration * min_stor
        data['MaxStorageLevel'] = value * duration * max_stor
        data['OutEff'] = self.grid.storage['OutEff']
        data['InEff'] = self.grid.storage['InEff']
        data['LossFactor'] = 0
        data['rho'] = 1
        self.grid.storage['StorageData'] = \
            self.grid.storage['StorageData'].append(data, ignore_index=True)


class Scaler(object):
    """Scales grid and input profiles using information stored in change table.

    :param dict scenario_info: scenario information.
    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    _gen_types = [
        'biomass', 'coal', 'dfo', 'geothermal', 'ng', 'nuclear', 'hydro',
        'solar', 'wind', 'wind_offshore', 'other']
    _thermal_gen_types = ['coal', 'dfo', 'geothermal', 'ng', 'nuclear']
    scale_keys = {
        'wind': {'wind', 'wind_offshore'},
        'solar': {'solar'},
        'hydro': {'hydro'},
        'demand': {'demand'}}

    def __init__(self, scenario_info, ssh_client):
        """Constructor.

        """
        pm = PrintManager()
        pm.block_print()
        self.scenario_id = scenario_info['id']
        self.interconnect = scenario_info['interconnect'].split('_')
        self._input = InputData(ssh_client)
        if scenario_info['change_table'] == 'Yes':
            self._load_ct()
        else:
            self.ct = {}
        self._load_grid()
        pm.enable_print()

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
                                self._grid.plant.loc[i, 'Pmax'] = \
                                    self._grid.plant.loc[i, 'Pmax'] * value
                                self._grid.plant.loc[i, 'Pmin'] = \
                                    self._grid.plant.loc[i, 'Pmin'] * value
                                if r in self._thermal_gen_types:
                                    self._grid.gencost[
                                        'before'].loc[i, 'c0'] = \
                                        self._grid.gencost[
                                            'before'].loc[i, 'c0'] * value
                                    if value == 0:
                                        continue
                                    self._grid.gencost[
                                        'before'].loc[i, 'c2'] = \
                                        self._grid.gencost[
                                            'before'].loc[i, 'c2'] / value
                    except KeyError:
                        pass
                    try:
                        for key, value in self.ct[r]['plant_id'].items():
                            self._grid.plant.loc[key, 'Pmax'] = \
                                self._grid.plant.loc[key, 'Pmax'] * value
                            self._grid.plant.loc[key, 'Pmin'] = \
                                self._grid.plant.loc[key, 'Pmin'] * value
                            if r in self._thermal_gen_types:
                                self._grid.gencost[
                                    'before'].loc[key, 'c0'] = \
                                    self._grid.gencost[
                                        'before'].loc[key, 'c0'] * value
                                if value == 0:
                                    continue
                                self._grid.gencost[
                                    'before'].loc[key, 'c2'] = \
                                    self._grid.gencost[
                                        'before'].loc[key, 'c2'] / value
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
                    data['MaxStorageLevel'] = \
                        value * storage['duration'] * storage['max_stor']
                    data['OutEff'] = storage['OutEff']
                    data['InEff'] = storage['InEff']
                    data['LossFactor'] = 0
                    data['rho'] = 1
                    storage['StorageData'] = storage['StorageData'].append(
                        data, ignore_index=True)
                self._grid.storage = storage
            if 'new_dcline' in list(self.ct.keys()):
                n_new_dcline = len(self.ct['new_dcline'])
                if self._grid.dcline.empty:
                    new_dcline_id = range(0, n_new_dcline)
                else:
                    max_dcline_id = self._grid.dcline.index.max()
                    new_dcline_id = range(max_dcline_id + 1,
                                          max_dcline_id + 1 + n_new_dcline)
                new_dcline = pd.DataFrame({c: [0] * n_new_dcline
                                           for c in self._grid.dcline.columns},
                                          index=new_dcline_id)
                for i, entry in zip(new_dcline_id, self.ct['new_dcline']):
                    from_interconnect = self._grid.bus.loc[entry[
                        'from_bus_id']].interconnect
                    to_interconnect = self._grid.bus.loc[entry[
                        'to_bus_id']].interconnect
                    new_dcline.loc[i, 'from_bus_id'] = entry['from_bus_id']
                    new_dcline.loc[i, 'to_bus_id'] = entry['to_bus_id']
                    new_dcline.loc[i, 'status'] = 1
                    new_dcline.loc[i, 'Pf'] = entry['capacity']
                    new_dcline.loc[i, 'Pt'] = 0.98 * entry['capacity']
                    new_dcline.loc[i, 'Pmin'] = -1 * entry['capacity']
                    new_dcline.loc[i, 'Pmax'] = entry['capacity']
                    new_dcline.loc[i, 'from_interconnect'] = from_interconnect
                    new_dcline.loc[i, 'to_interconnect'] = to_interconnect
                self._grid.dcline = self._grid.dcline.append(new_dcline)
            if 'new_branch' in list(self.ct.keys()):
                n_new_branch = len(self.ct['new_branch'])
                max_branch_id = self._grid.branch.index.max()
                new_branch_id = range(max_branch_id + 1,
                                      max_branch_id + 1 + n_new_branch)
                new_branch = pd.DataFrame({c: [0] * n_new_branch
                                           for c in self._grid.branch.columns},
                                          index=new_branch_id)
                v2x = voltage_to_x_per_distance(self._grid)
                for i, entry in zip(new_branch_id, self.ct['new_branch']):
                    interconnect = self._grid.bus.loc[entry[
                        'from_bus_id']].interconnect
                    from_zone_id = self._grid.bus.loc[entry[
                        'from_bus_id']].zone_id
                    to_zone_id = self._grid.bus.loc[entry['to_bus_id']].zone_id
                    from_zone_name = self._grid.id2zone[from_zone_id]
                    to_zone_name = self._grid.id2zone[to_zone_id]
                    from_lon = self._grid.bus.loc[entry['from_bus_id']].lon
                    from_lat = self._grid.bus.loc[entry['from_bus_id']].lat
                    to_lon = self._grid.bus.loc[entry['to_bus_id']].lon
                    to_lat = self._grid.bus.loc[entry['to_bus_id']].lat
                    from_basekv = v2x[self._grid.bus.loc[entry[
                        'from_bus_id']].baseKV]
                    to_basekv = v2x[self._grid.bus.loc[entry[
                        'to_bus_id']].baseKV]
                    distance = haversine((from_lat, from_lon), (to_lat, to_lon))
                    x = distance * np.mean([from_basekv, to_basekv])

                    new_branch.loc[i, 'from_bus_id'] = entry['from_bus_id']
                    new_branch.loc[i, 'to_bus_id'] = entry['to_bus_id']
                    new_branch.loc[i, 'status'] = 1
                    new_branch.loc[i, 'ratio'] = 0
                    new_branch.loc[i, 'branch_device_type'] = 'Line'
                    new_branch.loc[i, 'rateA'] = entry['capacity']
                    new_branch.loc[i, 'interconnect'] = interconnect
                    new_branch.loc[i, 'from_zone_id'] = from_zone_id
                    new_branch.loc[i, 'to_zone_id'] = to_zone_id
                    new_branch.loc[i, 'from_zone_name'] = from_zone_name
                    new_branch.loc[i, 'to_zone_name'] = to_zone_name
                    new_branch.loc[i, 'from_lon'] = from_lon
                    new_branch.loc[i, 'from_lat'] = from_lat
                    new_branch.loc[i, 'to_lon'] = to_lon
                    new_branch.loc[i, 'to_lat'] = to_lat
                    new_branch.loc[i, 'x'] = x
                self._grid.branch = self._grid.branch.append(new_branch)
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

        if (bool(self.ct)
                and bool(self.scale_keys[resource] & set(self.ct.keys()))):
            for subresource in self.scale_keys[resource]:
                try:
                    for key, value in self.ct[subresource]['zone_id'].items():
                        plant_id = self._original_grid.plant.groupby(
                            ['zone_id', 'type']).get_group(
                            (key, subresource)).index.values.tolist()
                        for i in plant_id:
                            profile.loc[:, i] *= value
                except KeyError:
                    pass
                try:
                    for key, value in self.ct[subresource]['plant_id'].items():
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


def voltage_to_x_per_distance(grid):
    """Calculates reactance per distance for voltage level.

    :param powersimdata.input.grid.Grid grid: a Grid object instance.
    :return: (*dict*) -- bus voltage to average reactance per mile.
    """
    branch = grid.branch[grid.branch.branch_device_type == 'Line']
    distance = branch[['from_lat', 'from_lon', 'to_lat', 'to_lon']].apply(
        lambda x: haversine((x[0], x[1]), (x[2], x[3])), axis=1).values

    no_zero = np.nonzero(distance)[0]
    x_per_distance = (branch.iloc[no_zero].x / distance[no_zero]).values

    basekv = np.array([grid.bus.baseKV[i]
                       for i in branch.iloc[no_zero].from_bus_id])

    v2x = {v: np.mean(x_per_distance[np.where(basekv == v)[0]])
           for v in set(basekv)}

    return v2x
