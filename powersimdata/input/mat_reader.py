import os
import pandas as pd
from scipy.io import loadmat

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.csv_reader import get_storage


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
        :raises IOError: if file does not exist.
        """
        if os.path.isfile(filename) is False:
            raise IOError('%s file not found' % filename)
        else:
            self.data_loc = filename

    def _build_network(self):
        data = loadmat(self.data_loc, squeeze_me=True, struct_as_record=False)

        self.branch, _ = frame('branch',
                               data['mdi'].mpc.branch,
                               data['mdi'].mpc.branchid)
        self.plant, storage_gen = frame('plant',
                                        data['mdi'].mpc.gen,
                                        data['mdi'].mpc.genid)
        self.gencost['after'], storage_gencost = frame('gencost_after',
                                                       data['mdi'].mpc.gencost,
                                                       data['mdi'].mpc.genid)

        if storage_gen is not None:
            self.storage = get_storage()
            self.storage['gen'] = storage_gen
            self.storage['gencost'] = storage_gencost
            col_name = self.storage['StorageData'].columns
            for c in col_name:
                self.storage['StorageData'][c] = eval('data["mdi"].Storage.'+c)
        else:
            self.storage = get_storage()

        """
        self.sub, _ = frame('sub',
                            data['mdi'].mpc.sub,
                            data['mdi'].mpc.subid)

        self.bus, _ = frame('bus',
                            data['mdi'].mpc.bus,
                            data['mdi'].mpc.busid)

        self.bus2sub, _ = frame('bus2sub',
                                data['mdi'].mpc.bus2sub,
                                data['mdi'].mpc.busid)

        self.dcline, _ = frame('dcline',
                               data['mdi'].mpc.dcline,
                               data['mdi'].mpc.dclineid)

        self.gencost['before'], _ = frame('gencost_before',
                                          data['mdi'].mpc.gencost_orig,
                                          data['mdi'].mpc.genid)
        self.interconnect = data['mdi'].mpc.interconnect
        self.id2zone = {k: self.id2zone[k] for k in self.bus.zone_id.unique()}
        self.zone2id = {value: key for key, value in self.id2zone.items()}
        """


def frame(name, table, index):
    """Builds data frame from MAT-file.

    :param str name: structure name.
    :param numpy.array table: table to be used to build data frame.
    :param numpy.array index: array to be used as data frame indices.
    :return: (tuple) -- first element is a data frame. Second element is None
        or a data frame when energy storage system are included.
    :raises ValueError: if name does not exist and table has wrong shape.
    """
    storage = None
    print('Loading %s' % name)
    if name.split('_')[0] == 'gencost':
        if table.shape[0] == index.shape[0]:
            data = format_gencost(pd.DataFrame(table, index=index))
        else:
            data = format_gencost(pd.DataFrame(table[:index.shape[0]],
                                               index=index))
            storage = format_gencost(pd.DataFrame(table[index.shape[0]:]))
    elif name in ['branch', 'bus', 'bus2sub', 'dcline', 'plant', 'sub']:
        col_name = column_name_provider()[name]
        expected_shape = (index.shape[0], len(col_name))
        if table.shape == expected_shape:
            data = pd.DataFrame(table, columns=col_name, index=index)
        else:
            data = pd.DataFrame(table[:index.shape[0]],
                                columns=col_name,
                                index=index)
            storage = pd.DataFrame(table[index.shape[0]:],
                                   columns=col_name)
    else:
        raise ValueError('Unknown %s table' % name)

    data.index.name = index_name_provider()[name]
    return data, storage


def index_name_provider():
    """Provides index name for data frame.

    :return: (*dict*) -- dictionary of data frame index name.
    """
    index_name = {'bus': 'bus_id',
                  'branch': 'branch_id',
                  'dcline': 'dcline_id',
                  'plant': 'plant_id',
                  'gencost_before': 'plant_id',
                  'gencost_after': 'plant_id'}
    return index_name


def column_name_provider():
    """Provides column names for data frame.

    :return: (*dict*) -- dictionary of data frame columns name.
    """
    col_name_bus = [
        'type', 'Pd', 'Qd', 'Gs', 'Bs', 'zone_id', 'Vm', 'Va', 'loss_zone',
        'baseKV', 'Vmax', 'Vmin', 'lam_P', 'lam_Q', 'mu_Vmax', 'mu_Vmin']
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
    col_name = {'bus': col_name_bus,
                'branch': col_name_branch,
                'dcline': col_name_dcline,
                'plant': col_name_plant,
                }
    return col_name


def format_gencost(data):
    """Modify generation cost data frame.

    :param pandas.DataFrame data: generation cost data frame.
    :return: (*pandas.DataFrame*) -- formatted data frame.
    :return: (pandas.DataFrame) -- formatted gencost data frame.
    """
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

    for row, plant_id in enumerate(gencost.index):
        n = gencost.loc[plant_id, 'n']
        if gencost.loc[plant_id, 'type'] == 2:
            for c in range(n):
                gencost.loc[plant_id, 'c'+str(n-c-1)] = data.iloc[row, 4+c]
        if gencost.loc[plant_id, 'type'] == 1:
            for c in range(n):
                p_val = data.iloc[row, 4+2*c]
                f_val = data.iloc[row, 4+2*c+1]
                gencost.loc[plant_id, 'p'+str(c+1)] = p_val
                gencost.loc[plant_id, 'f'+str(c+1)] = f_val
    return gencost
