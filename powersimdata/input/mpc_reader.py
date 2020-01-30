import pandas as pd

from powersimdata.input.helpers import csv_to_data_frame


class MPCReader(object):
    """MPC files reader

    """
    def __init__(self, data_loc):
        """Constructor

        :param str data_loc: path to data.
        """
        self.bus = csv_to_data_frame(data_loc, 'bus.csv')
        self.plant = csv_to_data_frame(data_loc, 'plant.csv')
        self.gencost = csv_to_data_frame(data_loc, 'gencost.csv')
        self.branch = csv_to_data_frame(data_loc, 'branch.csv')
        self.dcline = csv_to_data_frame(data_loc, 'dcline.csv')


def get_storage():
    """Get storage

    :return: (*dict*) -- storage structure for MATPOWER/MOST
    """
    storage = {
        'gen': pd.DataFrame(columns=[
            'bus_id', 'Pg', 'Qg', 'Qmax', 'Qmin', 'Vg', 'mBase', 'status',
            'Pmax', 'Pmin', 'Pc1', 'Pc2', 'Qc1min', 'Qc1max', 'Qc2min',
            'Qc2max', 'ramp_agc', 'ramp_10', 'ramp_30', 'ramp_q', 'apf']),
        'gencost': pd.DataFrame(columns=[
            'type', 'startup', 'shutdown', 'n', 'c2', 'c1', 'c0']),
        'StorageData': pd.DataFrame(columns=[
            'UnitIdx', 'InitialStorage', 'InitialStorageLowerBound',
            'InitialStorageUpperBound', 'InitialStorageCost',
            'TerminalStoragePrice', 'MinStorageLevel', 'MaxStorageLevel',
            'OutEff', 'InEff', 'LossFactor', 'rho']),
        'genfuel': [],
        'duration': None,       # hours
        'min_stor': None,       # ratio
        'max_stor': None,       # ratio
        'InEff': None,
        'OutEff': None,
        'energy_price': None    # $/MWh
        }
    return storage
