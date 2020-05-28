import copy
import numpy as np

from powersimdata.input.profiles import InputData
from powersimdata.utility.distance import haversine


class TransformGrid(object):
    """Transforms grid according to operations listed in change table.

    """

    def __init__(self, grid, ct):
        """Constructor

        :param powersimdata.input.grid.Grid grid: a Grid object.
        :param dict ct: change table.
        """
        self.grid = copy.deepcopy(grid)
        self.ct = copy.deepcopy(ct)
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
                    (zone_id, gen_type)).index.tolist()
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
                    (zone_id, zone_id)).index.tolist()
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
            self.grid.dcline.loc[dcline_id, 'Pmin'] *= factor
            self.grid.dcline.loc[dcline_id, 'Pmax'] *= factor
            if factor == 0:
                self.grid.dcline.loc[dcline_id, 'status'] = 0

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


class ScaleProfile(object):
    """Scales profiles according to scale factors listed in change table.

    """
    def __init__(self, ssh_client, scenario_id, grid, ct):
        """Constructor

        :param paramiko.client.SSHClient ssh_client: session with an SSH server.
        :param str scenario_id: scenario identification number.
        :param powersimdata.input.grid.Grid grid: a Grid object.
        :param dict ct: change table.
        """
        self._input_data = InputData(ssh_client)
        self.scenario_id = scenario_id
        self.grid = copy.deepcopy(grid)
        self.ct = copy.deepcopy(ct)
        self.scale_keys = {'wind': {'wind', 'wind_offshore'},
                           'solar': {'solar'},
                           'hydro': {'hydro'},
                           'demand': {'demand'}}

    def get_power_output(self, resource):
        """Returns scaled profile.

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

        profile = self._input_data.get_data(self.scenario_id, resource)

        if bool(self.ct) and \
                bool(self.scale_keys[resource] & set(self.ct.keys())):
            for r in self.scale_keys[resource]:
                if r in self.ct.keys() and 'zone_id' in self.ct[r].keys():
                    for z, f in self.ct[r]['zone_id'].items():
                        plant_id = self.grid.plant.groupby(
                            ['zone_id', 'type']).get_group(
                            (z, r)).index.values.tolist()
                        profile.loc[:, plant_id] *= f
                if r in self.ct.keys() and 'plant_id' in self.ct[r].keys():
                    for i, f in self.ct[r]['plant_id'].items():
                        profile.loc[:, i] *= f

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
        demand = self._input_data.get_data(self.scenario_id, 'demand')
        if bool(self.ct) and 'demand' in list(self.ct.keys()):
            for key, value in self.ct['demand']['zone_id'].items():
                print('Multiply demand in %s (#%d) by %.2f' %
                      (self.grid.id2zone[key], key, value))
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
