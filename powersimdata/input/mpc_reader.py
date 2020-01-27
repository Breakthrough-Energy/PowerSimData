import os
import pandas as pd


class MPCReader(object):
    """MPC files reader

    """
    def __init__(self, data_loc):
        """Constructor

        :param str data_loc: path to data.
        """
        self.data_loc = data_loc
        self._read_zone()
        self._read_sub()
        self._read_bus2sub()
        self._read_bus()
        self._read_plant()
        self._read_gencost()
        self._read_branch()
        self._read_dcline()
        self._add_extra_information_to_data_frame()

    def _read_branch(self):
        """Get branches.

        :return: (*pandas.DataFrame*) -- substations
        """
        print("Loading branch")
        self.branch = pd.read_csv(os.path.join(self.data_loc, 'branch.csv'),
                                  index_col=0, float_precision='high')

    def _read_sub(self):
        """Get substations.

        :return: (*pandas.DataFrame*) -- substations
        """
        print("Loading sub")
        self.sub = pd.read_csv(os.path.join(self.data_loc, 'sub.csv'),
                               index_col=0, float_precision='high')

    def _read_plant(self):
        """Get generators.

        :return: (*pandas.DataFrame*) -- generators.
        """
        print("Loading plant")
        self.plant = pd.read_csv(os.path.join(self.data_loc, 'plant.csv'),
                                 index_col=0, float_precision='high')

    def _read_gencost(self):
        """Get generation cost.

        :return: (*pandas.DataFrame*) -- generation cost.
        """
        print("Loading generation cost")
        self.gencost = pd.read_csv(os.path.join(self.data_loc, 'gencost.csv'),
                                   index_col=0, float_precision='high')

    def _read_dcline(self):
        """Get DC line.

         """
        print("Loading DC line")
        self.dcline = pd.read_csv(os.path.join(self.data_loc, 'dcline.csv'),
                                  index_col=0, float_precision='high')

    def _read_bus2sub(self):
        """Get bus to substation mapping.

        :return: (*pandas.DataFrame*) -- bus to substation correspondence.
        """
        print("Loading bus2sub")
        self.bus2sub = pd.read_csv(os.path.join(self.data_loc, 'bus2sub.csv'),
                                   index_col=0)

    def _read_bus(self):
        """Get bus.

        :return: (*pandas.DataFrame*) -- bus.
        """
        print("Loading bus")
        self.bus = pd.read_csv(os.path.join(self.data_loc, 'bus.csv'),
                               index_col=0, float_precision='high')

    def _read_zone(self):
        """Get load zone

        :return: (*pandas.DataFrame*) -- load zone.
        """
        print("Loading load zone")
        self.id2zone = pd.read_csv(os.path.join(self.data_loc, 'zone.csv'),
                                   index_col=0).zone_name.to_dict()
        self.zone2id = {value: key for key, value in self.id2zone.items()}

    def _add_extra_information_to_data_frame(self):
        """Adds columns to various data frames.

        """
        bus2zone = self.bus.zone_id.to_dict()
        bus2coord = pd.merge(self.bus2sub[['sub_id']], self.sub[['lat', 'lon']],
                             on='sub_id').set_index(self.bus2sub.index).drop(
            columns='sub_id').to_dict()
        self._add_column_to_bus(bus2coord)
        self._add_column_to_plant(bus2zone, bus2coord)
        self._add_column_to_branch(bus2zone, bus2coord)

    def _add_column_to_bus(self, bus2coord):
        """Adds columns to bus data frame

        :param dict bus2coord: bus to coordinates mapping.
        """
        self.bus['lat'] = [bus2coord['lat'][i] for i in self.bus.index]
        self.bus['lon'] = [bus2coord['lon'][i] for i in self.bus.index]

    def _add_column_to_plant(self, bus2zone, bus2coord):
        """Adds columns to plant data frame

        :param dict bus2zone: bus to zone mapping.
        :param dict bus2coord: bus to coordinates mapping.
        """
        self.plant['zone_id'] = [bus2zone[i] for i in self.plant.bus_id]
        self.plant['zone_name'] = [self.id2zone[i] for i in self.plant.zone_id]
        self.plant['lat'] = [bus2coord['lat'][i] for i in self.plant.bus_id]
        self.plant['lon'] = [bus2coord['lon'][i] for i in self.plant.bus_id]

    def _add_column_to_branch(self, bus2zone, bus2coord):
        """Adds columns to branch data frame

        :param dict bus2zone: bus to zone mapping.
        :param dict bus2coord: bus to coordinates mapping.
        """
        self.branch['from_zone_id'] = [bus2zone[i]
                                       for i in self.branch.from_bus_id]
        self.branch['to_zone_id'] = [bus2zone[i]
                                     for i in self.branch.to_bus_id]
        self.branch['from_zone_name'] = [self.id2zone[i]
                                         for i in self.branch.from_zone_id]
        self.branch['to_zone_name'] = [self.id2zone[i]
                                       for i in self.branch.to_zone_id]
        self.branch['from_lat'] = [bus2coord['lat'][i]
                                   for i in self.branch.from_bus_id]
        self.branch['from_lon'] = [bus2coord['lon'][i]
                                   for i in self.branch.from_bus_id]
        self.branch['to_lat'] = [bus2coord['lat'][i]
                                 for i in self.branch.to_bus_id]
        self.branch['to_lon'] = [bus2coord['lon'][i]
                                 for i in self.branch.to_bus_id]


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
