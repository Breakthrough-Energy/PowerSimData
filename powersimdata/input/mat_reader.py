import os
import pandas as pd
from scipy.io import loadmat

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.helpers import (add_coord_to_grid_data_frames,
                                        add_zone_to_grid_data_frames,
                                        add_interconnect_to_grid_data_frames)


class MATReader(AbstractGrid):
    """MATLAB file reader

    """
    def __init__(self, filename):
        """Constructor.

        :param filename: path to file
        """
        super().__init__()
        self._set_data_loc(filename)

        self._build_network()

    def _set_data_loc(self, filename):
        """Sets data location.

        :param str filename: path to file
        :raises FileNotFoundError: if file does not exist.
        """
        if os.path.isfile(filename) is False:
            raise FileNotFoundError('%s file not found' % filename)
        else:
            self.data_loc = filename

    def _build_network(self):
        data = loadmat(self.data_loc, squeeze_me=True, struct_as_record=False)
        mpc = data['mdi'].mpc
        try:
            n_storage = mpc.iess.shape[0]
        except AttributeError:
            n_storage = 0

        try:
            n_dcline = mpc.dclineid.shape[0]
        except AttributeError:
            n_dcline = 0

        # bus
        self.bus, _ = frame('bus', mpc.bus, mpc.busid)

        # plant
        self.plant, plant_storage = frame('plant',
                                          mpc.gen,
                                          mpc.genid,
                                          n_storage=n_storage)
        self.plant['type'] = mpc.genfuel[:len(mpc.genid)]
        self.plant['GenFuelCost'] = mpc.genfuelcost

        # heat rate curve
        self.heat_rate_curve, _ = frame('heat_rate_curve',
                                        mpc.heatratecurve,
                                        mpc.genid)

        # gencost before
        self.gencost['before'], _ = frame('gencost_before',
                                          mpc.gencost_orig,
                                          mpc.genid)

        # gencost after
        self.gencost['after'], gencost_storage = frame('gencost_after',
                                                       mpc.gencost,
                                                       mpc.genid,
                                                       n_storage=n_storage)

        # branch
        self.branch, _ = frame('branch', mpc.branch, mpc.branchid)
        self.branch['branch_device_type'] = mpc.branchdevicetype

        # DC line
        if n_dcline > 0:
            self.dcline, _ = frame('dcline', mpc.dcline, mpc.dclineid)

        # substation
        self.sub, _ = frame('sub', mpc.sub, mpc.subid)

        # bus to sub mapping
        self.bus2sub, _ = frame('bus2sub', mpc.bus2sub, mpc.busid)

        # zone
        zone = pd.DataFrame(mpc.zone, columns=['zone_id', 'zone_name'])
        self.zone2id = link(zone.zone_name.values, zone.zone_id.values)
        self.id2zone = link(zone.zone_id.values, zone.zone_name.values)

        # storage
        if n_storage > 0:
            self.storage['gen'] = plant_storage
            self.storage['gencost'] = gencost_storage
            col_name = self.storage['StorageData'].columns
            for c in col_name:
                self.storage['StorageData'][c] = eval('data["mdi"].Storage.'+c)

        # interconnect
        self.interconnect = self.sub.interconnect.unique().tolist()

        add_information_to_model(self)


def frame(name, table, index, n_storage=0):
    """Builds data frame from MAT-file.

    :param str name: structure name.
    :param numpy.array table: table to be used to build data frame.
    :param numpy.array index: array to be used as data frame indices.
    :param int n_storage: number of storage devices.
    :return: (tuple) -- first element is a data frame. Second element is None
        or a data frame when energy storage system are included.
    :raises ValueError: if name does not exist and table has wrong shape.
    """
    storage = None
    print('Loading %s' % name)
    if name.split('_')[0] == 'gencost':
        if table.shape[0] == index.shape[0]:
            data = format_gencost(pd.DataFrame(table, index=index))
        elif n_storage > 0:
            data = format_gencost(
                pd.DataFrame(table[:index.shape[0]], index=index))
            storage = format_gencost(
                pd.DataFrame(table[index.shape[0]:index.shape[0]+n_storage]))
        else:
            data = format_gencost(
                pd.DataFrame(table[:index.shape[0]], index=index))
    else:
        col_name = column_name_provider()[name]
        col_type = column_type_provider()[name]
        expected_shape = (index.shape[0], len(col_name))
        if table.shape == expected_shape:
            data = pd.DataFrame(table, columns=col_name, index=index)
        elif n_storage > 0:
            data = pd.DataFrame(
                table[:index.shape[0]], columns=col_name, index=index)
            storage = pd.DataFrame(
                table[index.shape[0]:index.shape[0]+n_storage:],
                columns=col_name)
        else:
            data = pd.DataFrame(
                table[:index.shape[0]], columns=col_name, index=index)
        data = data.astype(link(col_name, col_type))

    data.index.name = index_name_provider()[name]
    return data, storage


def link(keys, values):
    """Creates hash table

    :param numpy.array keys: key.
    :param numpy.array values: value.
    :return: (*dict*) -- hash table.
    """
    return {k: v for k, v in zip(keys, values)}


def index_name_provider():
    """Provides index name for data frame.

    :return: (*dict*) -- dictionary of data frame index name.
    """
    index_name = {'sub': 'sub_id',
                  'bus': 'bus_id',
                  'bus2sub': 'bus_id',
                  'branch': 'branch_id',
                  'dcline': 'dcline_id',
                  'plant': 'plant_id',
                  'gencost_before': 'plant_id',
                  'gencost_after': 'plant_id',
                  'heat_rate_curve': 'plant_id'}
    return index_name


def column_name_provider():
    """Provides column names for data frame.

    :return: (*dict*) -- dictionary of data frame columns name.
    """
    col_name_sub = [
        'name', 'interconnect_sub_id', 'lat', 'lon', 'interconnect']
    col_name_bus = [
        'bus_id', 'type', 'Pd', 'Qd', 'Gs', 'Bs', 'zone_id', 'Vm', 'Va',
        'loss_zone', 'baseKV', 'Vmax', 'Vmin', 'lam_P', 'lam_Q', 'mu_Vmax',
        'mu_Vmin']
    col_name_bus2sub = ['sub_id', 'interconnect']
    col_name_branch = [
        'from_bus_id', 'to_bus_id', 'r', 'x', 'b', 'rateA', 'rateB', 'rateC',
        'ratio', 'angle', 'status', 'angmin', 'angmax', 'Pf', 'Qf', 'Pt', 'Qt',
        'mu_Sf', 'mu_St', 'mu_angmin', 'mu_angmax']
    col_name_dcline = [
        'from_bus_id', 'to_bus_id', 'status', 'Pf', 'Pt', 'Qf', 'Qt', 'Vf',
        'Vt', 'Pmin', 'Pmax', 'QminF', 'QmaxF', 'QminT', 'QmaxT', 'loss0',
        'loss1', 'muPmin', 'muPmax', 'muQminF', 'muQmaxF', 'muQminT',
        'muQmaxT']
    col_name_plant = [
        'bus_id', 'Pg', 'Qg', 'Qmax', 'Qmin', 'Vg', 'mBase', 'status', 'Pmax',
        'Pmin', 'Pc1', 'Pc2', 'Qc1min', 'Qc1max', 'Qc2min', 'Qc2max',
        'ramp_agc', 'ramp_10', 'ramp_30', 'ramp_q', 'apf', 'mu_Pmax', 'mu_Pmin',
        'mu_Qmax', 'mu_Qmin']
    col_name_heat_rate_curve = ['GenIOB', 'GenIOC', 'GenIOD']
    col_name = {
        'sub': col_name_sub,
        'bus': col_name_bus,
        'bus2sub': col_name_bus2sub,
        'branch': col_name_branch,
        'dcline': col_name_dcline,
        'plant': col_name_plant,
        'heat_rate_curve': col_name_heat_rate_curve}
    return col_name


def column_type_provider():
    """Provides column types for data frame.

    :return: (*dict*) -- dictionary of data frame columns type.
    """
    col_type_sub = [
        'str', 'int', 'float', 'float', 'str']
    col_type_bus = [
        'int', 'int', 'float', 'float', 'int', 'float', 'int', 'float', 'float',
        'float', 'int', 'float', 'float', 'float', 'int', 'int', 'int']
    col_type_bus2sub = ['int', 'str']
    col_type_branch = [
        'int', 'int', 'float', 'float', 'float', 'float', 'int', 'int', 'float',
        'float', 'int', 'int', 'int', 'float', 'float', 'float', 'float',
        'int', 'int', 'int', 'int']
    col_type_dcline = [
        'int', 'int', 'int', 'int', 'float', 'float', 'float', 'float', 'float',
        'int', 'int', 'float', 'float', 'float', 'float', 'int', 'int', 'int',
        'int', 'int', 'int', 'int', 'int']
    col_type_plant = [
        'int', 'float', 'float', 'float', 'float', 'float', 'float', 'int',
        'float', 'float', 'int', 'int', 'int', 'int', 'int', 'int', 'int',
        'int', 'int', 'int', 'float', 'int', 'int', 'int', 'int']
    col_type_heat_rate_curve = ['float', 'float', 'float']
    col_type = {
        'sub': col_type_sub,
        'bus': col_type_bus,
        'bus2sub': col_type_bus2sub,
        'branch': col_type_branch,
        'dcline': col_type_dcline,
        'plant': col_type_plant,
        'heat_rate_curve': col_type_heat_rate_curve}
    return col_type


def format_gencost(data):
    """Modify generation cost data frame.

    :param pandas.DataFrame data: generation cost data frame.
    :return: (*pandas.DataFrame*) -- formatted data frame.
    :return: (pandas.DataFrame) -- formatted gencost data frame.
    """

    def parse_gencost_row(row, data, name2iloc):
        n = int(row['n'])
        data_index = name2iloc[row.name]
        if row['type'] == 2:
            for c in range(n):
                row['c'+str(n-c-1)] = data.iloc[data_index, 4+c]
        if row['type'] == 1:
            for c in range(n):
                p_val = data.iloc[data_index, 4+2*c]
                f_val = data.iloc[data_index, 4+2*c+1]
                row['p'+str(c+1)] = p_val
                row['f'+str(c+1)] = f_val
        return row

    gencost = data.iloc[:, [0, 1, 2, 3]].copy()
    gencost = gencost.astype({0: 'int', 1: 'float', 2: 'float', 3: 'int'})
    gencost.rename(columns={0: 'type', 1: 'startup', 2: 'shutdown', 3: 'n'},
                   inplace=True)

    if 2 in gencost.type.unique():
        n_max = gencost.groupby('type').get_group(2).n.max()
        for i in range(n_max):
            gencost['c'+str(n_max-i-1)] = [0.0] * gencost.shape[0]
    if 1 in gencost.type.unique():
        n_max = gencost.groupby('type').get_group(1).n.max()
        for i in range(n_max):
            gencost['p'+str(i+1)] = [0.0] * gencost.shape[0]
            gencost['f'+str(i+1)] = [0.0] * gencost.shape[0]

    name2iloc = {plant_id: row for row, plant_id in enumerate(gencost.index)}
    gencost = gencost.apply(parse_gencost_row, axis=1, args=(data, name2iloc))

    return gencost


def add_information_to_model(grid):
    """Makes a standard grid.

    :param powersimdata.input.MATReader grid: grid with missing information.
    """
    grid.bus.drop(columns=['bus_id'], inplace=True)

    def reset_id():
        return lambda x: grid.bus.index[x - 1]

    grid.plant['bus_id'] = grid.plant['bus_id'].apply(reset_id())
    grid.branch['from_bus_id'] = grid.branch['from_bus_id'].apply(reset_id())
    grid.branch['to_bus_id'] = grid.branch['to_bus_id'].apply(reset_id())
    grid.dcline['from_bus_id'] = grid.dcline['from_bus_id'].apply(reset_id())
    grid.dcline['to_bus_id'] = grid.dcline['to_bus_id'].apply(reset_id())

    add_interconnect_to_grid_data_frames(grid)
    add_zone_to_grid_data_frames(grid)
    add_coord_to_grid_data_frames(grid)

    grid.plant = grid.plant.join(grid.heat_rate_curve)
