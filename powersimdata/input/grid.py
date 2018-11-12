import os

import pandas as pd
import seaborn as sns

class Grid():
    
    top_dirname = os.path.dirname(__file__)
    data_dirname = os.path.join(top_dirname, 'data')
    
    
    ID2type = {0: 'wind', 1: 'solar', 2: 'hydro',
               3: 'ng', 4: 'nuclear', 5: 'coal'}
    type2ID = {v: k for k, v in ID2type.items()}
    
    type2color = {
        'wind': sns.xkcd_rgb["green"],
        'solar': sns.xkcd_rgb["amber"],
        'hydro': sns.xkcd_rgb["light blue"],
        'ng': sns.xkcd_rgb["orchid"],
        'nuclear': sns.xkcd_rgb["silver"],
        'coal': sns.xkcd_rgb["light brown"]}
    
    def __init__(self, name, load='network'):
        
        self.name = name
        self.data_loc = os.path.join(self.data_dirname, 'usa','')
        
        if name == 'TexasWestern':
            self._read_network_files()
            self.sub.drop(self.sub.groupby("interconnect").get_group("Eastern").index,inplace=True)
            self.bus2sub.drop(self.bus2sub.groupby("interconnect").get_group("Eastern").index,inplace=True)
            self.bus.drop(self.bus.groupby("interconnect").get_group("Eastern").index,inplace=True)
            self.genbus.drop(self.genbus.groupby("interconnect").get_group("Eastern").index,inplace=True)
            self.branches.drop(self.branches.groupby("interconnect").get_group("Eastern").index,inplace=True)
        elif name == 'USA':
            self._read_network_files()   
        else:
            print("Grid not available!")
            print("Choose between USA and TexasWestern")
            return
        print('Done loading')
        
    def _read_sub(self):
        """Read substation file and add data to `sub` pandas dataframe.
        
        """
        print('Loading sub')

        self.sub = pd.read_pickle(
            self.data_loc + 'USASubstations.pkl')

    def _read_bus2sub(self):
        """Read bus2sub file and add data to `bus2sub` pandas dataframe.
        
        """
        print('Loading bus2sub')

        self.bus2sub = pd.read_pickle(
            self.data_loc+'USAbus2sub.pkl')

    def _read_bus(self):
        """Read bus file and add data to `bus` pandas dataframe.
        
        """
        print('Loading bus')
        # Includes all the buses, demand and gen
        self.bus = pd.read_csv(
            self.data_loc+'bus_case.txt',
            sep=r'\s+'
        )
        self.bus.rename(columns={'bus_i': 'busID'}, inplace=True)
        self.bus['lat'] = self.sub.loc[
            self.bus2sub.loc[self.bus['busID'], 'subID'],
            'lat'
        ].values
        self.bus['lon'] = self.sub.loc[
            self.bus2sub.loc[self.bus['busID'], 'subID'],
            'lon'
        ].values
        
        self.bus["interconnect"] = "Eastern"
        self.bus.loc[self.bus.busID > 3000000,"interconnect"] = "Texas"
        self.bus.loc[(self.bus.busID > 2000000) & (self.bus.busID < 3000000),
                     "interconnect"] = "Western"

    def _read_gen_bus(self):
        """Read gen_bus file and add data to `genbus` pandas dataframe.
        
        """
        print('Loading genbus')
        self.genbus = pd.read_csv(
            self.data_loc+'genbus_case.txt',
            sep=r'\s+'
        )
        self.gentype = pd.read_csv(
            self.data_loc+'gentype_case.txt',
            sep=r'\s+',
            header=None
        )
        self.genbus['type'] = self.gentype
        self.genbus.rename(columns={'bus': 'busID'}, inplace=True)
        self.genbus['lat'] = self.sub.loc[
            self.bus2sub.loc[
                self.genbus['busID'], 'subID'
            ],
            'lat'
        ].values
        self.genbus['lon'] = self.sub.loc[
            self.bus2sub.loc[
                self.genbus['busID'],
                'subID'
            ],
            'lon'
        ].values
        self.genbus_aux = pd.read_pickle(
            self.data_loc+'USAgenbus_aux.pkl'
        )
        self.genbus = pd.concat([
            self.genbus,
            self.genbus_aux.reset_index()[['GenMWMax', 'GenMWMin']]
        ], axis=1)
        self.genbus.index.name = 'plantID'
        
        self.genbus["interconnect"] = "Eastern"
        self.genbus.loc[self.genbus.busID > 3000000,"interconnect"] = "Texas"
        self.genbus.loc[(self.genbus.busID > 2000000) & (self.genbus.busID < 3000000),
                     "interconnect"] = "Western"

    def _read_branches(self):
        """Read branches file and add data to `branches` pandas dataframe.
        
        """
        print('Loading branches')

        self.branches = pd.read_csv(
            self.data_loc+'branch_case.txt',
            sep=r'\s+'
        )

        self.branches['from_lat'] = self.sub.loc[
            self.bus2sub.loc[
                self.branches['fbus'],
                'subID'
            ],
            'lat'
        ].values
        self.branches['from_lon'] = self.sub.loc[
            self.bus2sub.loc[
                self.branches['fbus'], 'subID'
            ],
            'lon'
        ].values
        self.branches['to_lat'] = self.sub.loc[
            self.bus2sub.loc[
                self.branches['tbus'], 'subID'
            ],
            'lat'
        ].values
        self.branches['to_lon'] = self.sub.loc[
            self.bus2sub.loc[
                self.branches['tbus'], 'subID'
            ],
            'lon'
        ].values

        self.branches["interconnect"] = "Eastern"
        self.branches.loc[self.branches.fbus > 3000000,"interconnect"] = "Texas"
        self.branches.loc[(self.branches.fbus > 2000000) & (self.branches.fbus < 3000000),
                     "interconnect"] = "Western"
        


    def _read_network_files(self):
        """Read all network file.
        
        """
        self._read_sub()
        self._read_bus2sub()
        self._read_bus()
        self._read_gen_bus()
        self._read_branches()
