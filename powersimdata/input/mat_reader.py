import os
import pandas as pd
from scipy.io import loadmat

from powersimdata.input.abstract_grid import AbstractGrid


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
        self.plant = get_plant(data['mdi'].mpc.gen,
                               data['mdi'].mpc.genid)
        self.branch = get_branch(data['mdi'].mpc.branch,
                                 data['mdi'].mpc.branchid)
        """
        self.bus = get_bus(data['mdi'].mpc.bus, 
                           data['mdi'].mpc.busid)
        self.dcline = get_dcline(data['mdi'].mpc.dcline, 
                           data['mdi'].mpc.dclineid)
        self.gencost['before'] = get_gencost(data['mdi'].mpc.gencost_before,
                                             data['mdi'].mpc.genid)
        self.gencost['after'] = get_gencost(data['mdi'].mpc.gencost_after,
                                            data['mdi'].mpc.genid),
        """


def get_bus(table, index):
    """Sets bus data frame.

    :param numpy.array table: bus table enclosed in MAT-file.
    :param numpy.array index: array of bus ids enclosed in MAT-file.
    :return: (pandas.DataFrame) -- bus data frame.
    """
    col_name = [
        'type', 'Pd', 'Qd', 'Gs', 'Bs', 'zone_id', 'Vm', 'Va', 'loss_zone',
        'baseKV', 'Vmax', 'Vmin', 'lam_P', 'lam_Q', 'mu_Vmax', 'mu_Vmin']
    bus = pd.DataFrame(table, columns=col_name, index=index)
    bus.index.name = 'bus_id'
    return bus


def get_branch(table, index):
    """Sets branch data frame.

    :param numpy.array table: branch table enclosed in MAT-file.
    :param numpy.array index: array of branch ids enclosed in MAT-file.
    :return: (pandas.DataFrame) -- branch data frame.
    """
    col_name = [
        'from_bus_id', 'to_bus_id', 'r', 'x', 'b', 'rateA', 'rateB', 'rateC',
        'ratio', 'angle', 'status', 'angmin', 'angmax', 'Pf', 'Qf', 'Pt', 'Qt',
        'mu_Sf', 'mu_St', 'mu_angmin', 'mu_angmax']
    branch = pd.DataFrame(table, columns=col_name, index=index)
    branch.index.name = 'bus_id'
    return branch


def get_dcline(table, index):
    """Sets dcline data frame.

    :param numpy.array table: dcline table enclosed in MAT-file.
    :param numpy.array index: array of dcline ids enclosed in MAT-file.
    :return: (pandas.DataFrame) -- dcline data frame.
    """
    col_name = [
        'from_bus_id', 'to_bus_id', 'status', 'Pf', 'Pt', 'Qf', 'Qt', 'Vf',
        'Vt', 'Pmin', 'Pmax', 'QminF', 'QmaxF', 'QminT', 'QmaxT', 'loss0',
        'loss1', 'muPmin', 'muPmax', 'muQminF', 'muQmaxF', 'muQminT',
        'muQmaxT']
    dcline = pd.DataFrame(table, columns=col_name, index=index)
    dcline.index.name = 'dcline_id'
    return dcline


def get_plant(table, index):
    """Sets plant data frame.

    :param numpy.array table: plant table enclosed in MAT-file.
    :param numpy.array index: array of plant ids enclosed in MAT-file.
    :return: (pandas.DataFrame) -- plant data frame.
    """
    col_name = [
        'bus_id', 'Pg', 'Qg', 'Qmax', 'Qmin', 'Vg', 'mBase', 'status', 'Pmax',
        'Pmin', 'Pc1', 'Pc2', 'Qc1min', 'Qc1max', 'Qc2min', 'Qc2max',
        'ramp_agc', 'ramp_10', 'ramp_30', 'ramp_q', 'apf', 'mu_Pmax', 'mu_Pmin',
        'mu_Qmax', 'mu_Qmin']
    plant = pd.DataFrame(table, columns=col_name, index=index)
    plant.index.name = 'plant_id'
    return plant


def get_gencost(table, index):
    """Sets gencost data frame.

    :param numpy.array table: generation cost table enclosed in MAT-file.
    :param numpy.array index: array of plant indices enclosed in MAT-file.
    :return: (pandas.DataFrame) -- gencost data frame.
    """
    gencost = pd.DataFrame(table, index=index)
    gencost = format_gencost(gencost)
    gencost.index.name = 'plant_id'
    return gencost


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
