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
        self.gencost = get_gencost(data['mdi'].mpc.gencost,
                                   data['mdi'].mpc.genid)


def get_plant(table, index):
    """Sets plant data frame.

    :param numpy.array table: plant table  enclosed in MAT-file.
    :param numpy.array index: array of plant ids enclosed in MAT-file.
    """
    col_name = [
        'bus_id', 'Pg', 'Qg', 'Qmax', 'Qmin', 'Vg', 'mBase', 'status',
        'Pmax', 'Pmin', 'Pc1', 'Pc2', 'Qc1min', 'Qc1max', 'Qc2min',
        'Qc2max', 'ramp_agc', 'ramp_10', 'ramp_30', 'ramp_q', 'apf',
        'mu_Pmax', 'mu_Pmin', 'mu_Qmax', 'mu_Qmin']
    plant = pd.DataFrame(table, columns=col_name, index=index)
    plant.index.name = 'plant_id'
    return plant


def get_gencost(table, index):
    """Sets gencost data frame.

    :param numpy.array table: generation cost table enclosed in MAT-file.
    :param numpy.array index: array of plant indices enclosed in MAT-file.
    """
    gencost = pd.DataFrame(table, index=index)
    gencost = format_gencost(gencost)
    gencost.index.name = 'plant_id'
    return gencost


def format_gencost(data):
    """Modify generation cost data frame.

    :param pandas.DataFrame data: generation cost data frame.
    :return: (*pandas.DataFrame*) -- formatted data frame.
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
