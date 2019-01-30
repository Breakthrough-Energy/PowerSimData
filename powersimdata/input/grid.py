import os

import pandas as pd
import seaborn as sns


class Grid():
    """Synthetic Network.

    :param list interconnect: name of interconnect(s).

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
        top_dirname = os.path.dirname(__file__)
        data_dirname = os.path.join(top_dirname, 'data')
        self.data_loc = os.path.join(data_dirname, 'usa', '')

        self._check_interconnect(interconnect)
        self._build_network()
        self._add_column()
        print("Done loading")

    def _check_interconnect(self, interconnect):
        """Checks if interconnect exists.

        :param list interconnect: interconnect name(s).
        """
        possible = ['USA', 'Eastern', 'Texas', 'Western']
        if isinstance(interconnect, str):
            test = [interconnect]
        elif isinstance(interconnect, list):
            test = interconnect
        else:
            raise TypeError("List of strings is expected for interconnect")

        for t in test:
            if t not in possible:
                raise NameError("%s not available. Choose among %s" %
                                (t, " / ".join(possible)))

        self.interconnect = test

    def _build_network(self):
        """Builds betwork.

        """
        self._read_network()
        if 'USA' not in self.interconnect:
            drop = ['Eastern', 'Texas', 'Western']
            for i in self.interconnect:
                drop.remove(i)
            for d in drop:
                self.sub.drop(self.sub.groupby(
                    'interconnect').get_group(d).index, inplace=True)
                self.bus2sub.drop(self.bus2sub.groupby(
                    'interconnect').get_group(d).index, inplace=True)
                self.bus.drop(self.bus.groupby(
                    'interconnect').get_group(d).index, inplace=True)
                self.plant.drop(self.plant.groupby(
                    'interconnect').get_group(d).index, inplace=True)
                self.branch.drop(self.branch.groupby(
                    'interconnect').get_group(d).index, inplace=True)

    def _add_column(self):
        """Add information in data frames.

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
        self.plant['zone_name'] = [self.load_zone[i]
                                   for i in self.plant.zone_id]

        self.branch['from_zone_id'] = [bus2zone[i]
                                       for i in self.branch.from_bus_id]
        self.branch['to_zone_id'] = [bus2zone[i]
                                     for i in self.branch.to_bus_id]
        self.branch['from_zone_name'] = [self.load_zone[i]
                                         for i in self.branch.from_zone_id]
        self.branch['to_zone_name'] = [self.load_zone[i]
                                       for i in self.branch.to_zone_id]

    def _read_network(self):
        """Reads all network file.

        """
        self._read_load_zone()
        self._read_sub()
        self._read_bus2sub()
        self._read_bus()
        self._read_plant()
        self._read_branch()

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
        plant_type = pd.read_csv(self.data_loc+'gentype_case.txt',
                                 sep=r'\s+', header=None)
        self.plant = pd.read_csv(self.data_loc+'genbus_case.txt', sep=r'\s+')
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

    def _read_load_zone(self):
        """Reads load zone files.

        """
        print("Loading zone")
        self.load_zone = pd.read_csv(self.data_loc + 'USAArea.csv',
                                     header=None,
                                     index_col=0,
                                     names=['zone_name']).zone_name.to_dict()
