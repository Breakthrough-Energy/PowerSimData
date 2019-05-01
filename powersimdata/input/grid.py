import os

import pandas as pd
import seaborn as sns


class Grid(object):
    """Synthetic Network.

    """
    id2type = {0: 'wind',
               1: 'solar',
               2: 'hydro',
               3: 'ng',
               4: 'nuclear',
               5: 'coal'}

    type2id = {v: k for k, v in id2type.items()}

    type2color = {'wind': sns.xkcd_rgb["green"],
                  'solar': sns.xkcd_rgb["amber"],
                  'hydro': sns.xkcd_rgb["light blue"],
                  'ng': sns.xkcd_rgb["orchid"],
                  'nuclear': sns.xkcd_rgb["silver"],
                  'coal': sns.xkcd_rgb["light brown"]}

    def __init__(self, interconnect):
        """Constructor.

        :param list interconnect: name of interconnect(s).
        """
        top_dirname = os.path.dirname(__file__)
        data_dirname = os.path.join(top_dirname, 'data')
        self.data_loc = os.path.join(data_dirname, 'usa', '')

        self._set_interconnect(interconnect)
        self._build_network()
        self._add_information()

    def _set_interconnect(self, interconnect):
        """Sets interconnect.

        :param list interconnect: interconnect name(s).
        :raises TypeError: if parameter has wrong type.
        :raises Exception: if interconnect not found or combination of \
            interconnect is not appropriate.
        """
        possible = ['Eastern', 'Texas', 'Western', 'USA']
        if not isinstance(interconnect, list):
            raise TypeError("List of string(s) is expected for interconnect")

        for i in interconnect:
            if i not in possible:
                raise Exception("Wrong interconnect. Choose from %s" %
                                " | ".join(possible))
        n = len(interconnect)
        if n > len(set(interconnect)):
            raise Exception("List of interconnects contains duplicate values")
        if 'USA' in interconnect and n > 1:
            raise Exception("USA interconnect cannot be paired")

        self.interconnect = interconnect

    def _build_network(self):
        """Builds network.

        """
        self._read_network()
        if 'USA' not in self.interconnect:
            drop = {'Eastern': [1, 52],
                    'Texas': [301, 308],
                    'Western': [201, 216]}
            for i in self.interconnect:
                del drop[i]
            for k, v in drop.items():
                self.sub.drop(self.sub.groupby(
                    'interconnect').get_group(k).index, inplace=True)
                self.bus2sub.drop(self.bus2sub.groupby(
                    'interconnect').get_group(k).index, inplace=True)
                self.bus.drop(self.bus.groupby(
                    'interconnect').get_group(k).index, inplace=True)
                self.plant.drop(self.plant.groupby(
                    'interconnect').get_group(k).index, inplace=True)
                self.gencost.drop(self.gencost.groupby(
                    'interconnect').get_group(k).index, inplace=True)
                try:
                    self.dcline.drop(self.dcline.groupby(
                        'from_interconnect').get_group(k).index, inplace=True)
                except KeyError:
                    pass
                try:
                    self.dcline.drop(self.dcline.groupby(
                        'to_interconnect').get_group(k).index, inplace=True)
                except KeyError:
                    pass
                self.branch.drop(self.branch.groupby(
                    'interconnect').get_group(k).index, inplace=True)
                for i in range(v[0], v[1] + 1):
                    del self.zone[i]

    def _add_information(self):
        """Adds information to data frames.

        """
        bus2zone = self.bus.zone_id.to_dict()
        bus2coord = pd.merge(self.bus2sub[['sub_id']],
                             self.sub[['lat', 'lon']],
                             on='sub_id').set_index(self.bus2sub.index).drop(
            columns='sub_id').to_dict()

        # Coordinates
        self.bus['lat'] = [bus2coord['lat'][i] for i in self.bus.index]
        self.bus['lon'] = [bus2coord['lon'][i] for i in self.bus.index]

        self.plant['lat'] = [bus2coord['lat'][i] for i in self.plant.bus_id]
        self.plant['lon'] = [bus2coord['lon'][i] for i in self.plant.bus_id]

        self.branch['from_lat'] = [bus2coord['lat'][i]
                                   for i in self.branch.from_bus_id]
        self.branch['from_lon'] = [bus2coord['lon'][i]
                                   for i in self.branch.from_bus_id]
        self.branch['to_lat'] = [bus2coord['lat'][i]
                                 for i in self.branch.to_bus_id]
        self.branch['to_lon'] = [bus2coord['lon'][i]
                                 for i in self.branch.to_bus_id]

        # Zoning
        self.plant['zone_id'] = [bus2zone[i] for i in self.plant.bus_id]
        self.plant['zone_name'] = [self.zone[i]
                                   for i in self.plant.zone_id]

        self.branch['from_zone_id'] = [bus2zone[i]
                                       for i in self.branch.from_bus_id]
        self.branch['to_zone_id'] = [bus2zone[i]
                                     for i in self.branch.to_bus_id]
        self.branch['from_zone_name'] = [self.zone[i]
                                         for i in self.branch.from_zone_id]
        self.branch['to_zone_name'] = [self.zone[i]
                                       for i in self.branch.to_zone_id]

    def _read_network(self):
        """Reads all network file.

        """
        print("# Loading %s interconnect" % "+".join(self.interconnect))
        self._read_zone()
        self._read_sub()
        self._read_bus2sub()
        self._read_bus()
        self._read_plant()
        self._read_gencost()
        self._read_branch()
        self._read_dcline()
        print("--> Done loading")

    def _read_sub(self):
        """Reads the substation file.

        """
        print("Loading sub")

        self.sub = pd.read_pickle(self.data_loc + 'USASubstations.pkl')
        self.sub.rename(columns={'intercon_subID': 'interconnect_sub_id'},
                        inplace=True)
        self.sub.index.name = 'sub_id'

    def _read_bus2sub(self):
        """Reads bus2sub file.

        """
        print("Loading bus2sub")
        self.bus2sub = pd.read_pickle(self.data_loc + 'USAbus2sub.pkl')
        self.bus2sub.index.name = 'bus_id'
        self.bus2sub.rename(columns={'subID': 'sub_id'}, inplace=True)

    def _read_bus(self):
        """Reads bus file.

        """
        print("Loading bus")

        # Read and format
        self.bus = pd.read_csv(self.data_loc + 'bus_case.txt', index_col=0,
                               sep=r'\s+')
        self.bus.index.name = 'bus_id'
        self.bus.drop(columns='zone', inplace=True)
        self.bus.rename(columns={'area': 'zone_id'}, inplace=True)

        # Interconnect
        self.bus["interconnect"] = "Eastern"
        self.bus.loc[self.bus.index > 2000000, 'interconnect'] = 'Western'
        self.bus.loc[self.bus.index > 3000000, 'interconnect'] = 'Texas'

    def _read_plant(self):
        """Reads generator files.

        """
        print("Loading plant")
        # Read and format
        plant_type = pd.read_csv(self.data_loc + 'gentype_case.txt',
                                 sep=r'\s+', header=None)
        self.plant = pd.read_csv(self.data_loc + 'genbus_case.txt', sep=r'\s+')
        self._plant_aux = pd.read_pickle(self.data_loc + 'USAgenbus_aux.pkl')
        self.plant.index.name = 'plant_id'
        self.plant.rename(columns={'bus': 'bus_id'}, inplace=True)

        # Combine
        self.plant = pd.concat([self.plant,
                                self._plant_aux.reset_index()[
                                    ['GenMWMax', 'GenMWMin']]],
                               axis=1)
        self.plant['type'] = plant_type

        # Interconnect
        self.plant['interconnect'] = 'Eastern'
        self.plant.loc[self.plant.bus_id > 2000000, 'interconnect'] = 'Western'
        self.plant.loc[self.plant.bus_id > 3000000, 'interconnect'] = 'Texas'

    def _read_gencost(self):
        """Reads generator cost file.

        """
        print("Loading plant cost")
        # Read and format
        self.gencost = pd.read_csv(self.data_loc + 'gencost_case.txt', sep=r'\s+')
        self.gencost.index.name = 'plant_id'

        # Interconnect
        self.gencost['interconnect'] = self.plant.interconnect

    def _read_dcline(self):
        """Reads DC line file.

        """
        print("Loading DC line")
        # Read and format
        self.dcline = pd.read_csv(self.data_loc + 'dcline_case.txt', sep=r'\s+')
        self.dcline.rename(columns={'fbus': 'from_bus_id',
                                    'tbus': 'to_bus_id'}, inplace=True)
        self.dcline.index.name = 'dcline_id'

        # Interconnect
        self.dcline['from_interconnect'] = 'Eastern'
        self.dcline['to_interconnect'] = 'Eastern'
        self.dcline.loc[self.dcline.from_bus_id > 2000000,
                        'from_interconnect'] = 'Western'
        self.dcline.loc[self.dcline.to_bus_id > 2000000,
                        'to_interconnect'] = 'Western'
        self.dcline.loc[self.dcline.from_bus_id > 3000000,
                        'from_interconnect'] = 'Texas'
        self.dcline.loc[self.dcline.to_bus_id > 3000000,
                        'to_interconnect'] = 'Texas'

    def _read_branch(self):
        """Reads branch file.

        """
        print("Loading branch")
        self.branch = pd.read_csv(self.data_loc + 'branch_case.txt',
                                  sep=r'\s+')
        self.branch.rename(columns={'fbus': 'from_bus_id',
                                    'tbus': 'to_bus_id'}, inplace=True)
        self.branch.index.name = 'branch_id'

        # Interconnect
        self.branch['interconnect'] = 'Eastern'
        self.branch.loc[self.branch.from_bus_id > 2000000,
                        'interconnect'] = 'Western'
        self.branch.loc[self.branch.from_bus_id > 3000000,
                        'interconnect'] = 'Texas'

    def _read_zone(self):
        """Reads load zone files.

        """
        print("Loading zone")
        self.zone = pd.read_csv(self.data_loc + 'USAArea.csv',
                                header=None,
                                index_col=0,
                                names=['zone_name']).zone_name.to_dict()
