import os

import pandas as pd
import seaborn as sns


class Grid():
    """Synthetic Network.

    :param str name: name of synthetic network.

    """
    top_dirname = os.path.dirname(__file__)
    data_dirname = os.path.join(top_dirname, 'data')

    ID2type = {0: 'wind',
               1: 'solar',
               2: 'hydro',
               3: 'ng',
               4: 'nuclear',
               5: 'coal'}

    type2ID = {v: k for k, v in ID2type.items()}

    type2color = {'wind': sns.xkcd_rgb["green"],
                  'solar': sns.xkcd_rgb["amber"],
                  'hydro': sns.xkcd_rgb["light blue"],
                  'ng': sns.xkcd_rgb["orchid"],
                  'nuclear': sns.xkcd_rgb["silver"],
                  'coal': sns.xkcd_rgb["light brown"]}

    def __init__(self, name):
        self.data_loc = os.path.join(self.data_dirname, 'usa', '')

        if name == 'Western':
            self._read_network_files()
            for n in ['Eastern', 'Texas']:
                self.sub.drop(self.sub.groupby(
                    'interconnect').get_group(n).index, inplace=True)
                self.bus2sub.drop(self.bus2sub.groupby(
                    'interconnect').get_group(n).index, inplace=True)
                self.bus.drop(self.bus.groupby(
                    'interconnect').get_group(n).index, inplace=True)
                self.genbus.drop(self.genbus.groupby(
                    'interconnect').get_group(n).index, inplace=True)
                self.branches.drop(self.branches.groupby(
                    'interconnect').get_group(n).index, inplace=True)
        elif name == 'TexasWestern':
            self._read_network_files()
            self.sub.drop(self.sub.groupby(
                'interconnect').get_group('Eastern').index, inplace=True)
            self.bus2sub.drop(self.bus2sub.groupby(
                'interconnect').get_group('Eastern').index, inplace=True)
            self.bus.drop(self.bus.groupby(
                'interconnect').get_group('Eastern').index, inplace=True)
            self.genbus.drop(self.genbus.groupby(
                'interconnect').get_group('Eastern').index, inplace=True)
            self.branches.drop(self.branches.groupby(
                'interconnect').get_group('Eastern').index, inplace=True)
        elif name == 'USA':
            self._read_network_files()
        else:
            print("Grid not available!")
            print("Choose between USA, TexasWestern and Western")
            return
        print("Done loading")

    def _read_sub(self):
        """Reads the substation file and add information to data frame.

        """
        print("Loading sub")

        self.sub = pd.read_pickle(self.data_loc + 'USASubstations.pkl')

    def _read_bus2sub(self):
        """Reads bus2sub file and add information to data frame.

        """
        print("Loading bus2sub")

        self.bus2sub = pd.read_pickle(self.data_loc + 'USAbus2sub.pkl')

    def _read_bus(self):
        """Reads bus file and add information to data frame, including \ 
            demand and generators.

        """
        print("Loading bus")

        self.bus = pd.read_csv(self.data_loc + 'bus_case.txt', sep=r'\s+')
        self.bus.rename(columns={'bus_i': 'busID'}, inplace=True)
        self.bus['lat'] = self.sub.loc[
            self.bus2sub.loc[self.bus['busID'], 'subID'], 'lat'].values
        self.bus['lon'] = self.sub.loc[
            self.bus2sub.loc[self.bus['busID'], 'subID'], 'lon'].values

        self.bus["interconnect"] = "Eastern"
        self.bus.loc[self.bus.busID > 3000000, 'interconnect'] = 'Texas'
        self.bus.loc[(self.bus.busID > 2000000) & (self.bus.busID < 3000000),
                     'interconnect'] = 'Western'

    def _read_gen_bus(self):
        """Reads gen_bus file and add information to data frame.

        """
        print("Loading genbus")

        self.genbus = pd.read_csv(self.data_loc+'genbus_case.txt', sep=r'\s+')
        self.gentype = pd.read_csv(self.data_loc+'gentype_case.txt',
                                   sep=r'\s+', header=None)
        self.genbus['type'] = self.gentype
        self.genbus.rename(columns={'bus': 'busID'}, inplace=True)
        self.genbus['lat'] = self.sub.loc[
            self.bus2sub.loc[self.genbus['busID'], 'subID'], 'lat'].values
        self.genbus['lon'] = self.sub.loc[
            self.bus2sub.loc[self.genbus['busID'], 'subID'], 'lon'].values
        self.genbus_aux = pd.read_pickle(self.data_loc + 'USAgenbus_aux.pkl')
        self.genbus = pd.concat([
            self.genbus,
            self.genbus_aux.reset_index()[['AreaNum', 'GenMWMax', 'GenMWMin']]
        ], axis=1)

        self.genbus['interconnect'] = 'Eastern'
        self.genbus.loc[self.genbus.busID > 3000000, 'interconnect'] = 'Texas'
        self.genbus.loc[
            (self.genbus.busID > 2000000) & (self.genbus.busID < 3000000),
            'interconnect'] = 'Western'

        self.genbus['newPlantID'] = self.genbus.index
        self.genbus.loc[
            self.genbus['interconnect'] == 'Texas',
            'newPlantID'] = range(3000000, 3000000 +
                                  sum(self.genbus['interconnect'] == 'Texas'))

        self.genbus.loc[
            self.genbus['interconnect'] == 'Western',
            'newPlantID'] = range(2000000, 2000000 +
                                  sum(self.genbus[
                                        'interconnect'] == 'Western'))
        self.genbus.set_index('newPlantID', inplace=True)

        self.genbus.loc[
            self.genbus['interconnect'] == 'Texas', 'AreaNum'] += 300

        self.genbus.loc[
            self.genbus["interconnect"] == 'Western', 'AreaNum'] += 200

        self.genbus['ZoneName'] = self.genbus.AreaNum.apply(
            lambda AreaNum: self.load_zones.loc[AreaNum])

        self.genbus.index.name = 'plantID'

    def _read_branches(self):
        """Reads branches file and add information to data frame.

        """
        print("Loading branches")

        self.branches = pd.read_csv(self.data_loc + 'branch_case.txt',
                                    sep=r'\s+')

        self.branches['from_lat'] = self.sub.loc[
            self.bus2sub.loc[self.branches['fbus'], 'subID'], 'lat'].values
        self.branches['from_lon'] = self.sub.loc[
            self.bus2sub.loc[self.branches['fbus'], 'subID'], 'lon'].values
        self.branches['to_lat'] = self.sub.loc[
            self.bus2sub.loc[self.branches['tbus'], 'subID'], 'lat'].values
        self.branches['to_lon'] = self.sub.loc[
            self.bus2sub.loc[self.branches['tbus'], 'subID'], 'lon'].values

        self.branches['interconnect'] = 'Eastern'
        self.branches.loc[
            self.branches.fbus > 3000000, 'interconnect'] = 'Texas'
        self.branches.loc[
            (self.branches.fbus > 2000000) & (self.branches.fbus < 3000000),
            'interconnect'] = 'Western'

    def _read_load_zones(self):
        """Reads load zone names

        """

        self.load_zones = pd.read_csv(self.data_loc + 'USAArea.csv',
                                      header=None, index_col=0,)

    def _read_network_files(self):
        """Reads all network file.

        """

        self._read_load_zones()
        self._read_sub()
        self._read_bus2sub()
        self._read_bus()
        self._read_gen_bus()
        self._read_branches()
