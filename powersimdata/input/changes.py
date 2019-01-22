import pandas as pd

from powersimdata.input.grid import Grid


class Change():
    """Handle changes that need to be applied to the original grid as well \ 
        as to the original demand, hydro, solar and wind profiles. A pickle \ 
        file enclosing the change table in form of a dictionary will be \ 
        created and trasfered on the server. Keys are *'grid'*, *'demand'*, \ 
        *'hydro'*, *'solar'* and *'wind'*. If a key is missing, it will be \ 
        assumed that the original grid of profile(s) should be considered, \ 
        i.e., no changes should be applied.  The data structure is given \ 
        below:
        
        * *'demand'*: \ 
            value is a dictionnary, which has load zones as keys and a \ 
            factor indicating the desired increase/decrease of load in zone \ 
            (1.2 would correspond to a 20% increase while 0.95 would be a 5% \ 
            decrease).
        * *'hydro'*, *'solar'* and *'wind'*: \ 
            value is a dictionary, which has the plant id as key and a \ 
            factor indicating the desired increase/decrease of capacity of \ 
            the plant (1.2 would correspond to a 20% increase while 0.95 \ 
            would be a 5% decrease).
        

    :param str name: name of scenario.
    :param str interconnect: name of interconnect.
    """

    def __init__(self, name, interconnect):
        self.name = name

        # Check interconnect exists
        self._check_interconnect(interconnect)

        # Set attribute
        self.interconnect = interconnect
        self.grid = Grid(interconnect)
        self.table = {}

    @staticmethod
    def _check_interconnect(interconnect):
        """Checks if interconnect exists.

        param str interconnect: name of interconnect.
        """
        possible = ['Western', 'TexasWestern', 'USA']
        if interconnect not in possible:
            print("%s is not an interconnect. Choose one of:" % interconnect)
            for p in possible:
                print(p)
            raise Exception('Invalid resource(s)')

    def _check_zones(self, zones):
        """Test zones.

        :param list zones: geographical zones.
        :raise Exception: if zone(s) are invalid.
        """
        possible = list(self.grid.genbus.ZoneName.unique())
        possible += [self.interconnect]
        if self.interconnect == 'Western':
            possible += ['California']
        for z in zones:
            if z not in possible:
                print("%s is not in %s interconnect. Possible zones are:" %
                      (z, self.interconnect))
                for p in possible:
                    print(p)
                raise Exception('Invalid zone(s)')

    def _get_plant_id(self, zone, resource):
        """Extracts the plant identification number of all the generators \ 
            located in one zone and using one specific resource.

        :param str zone: zone to consider.
        :param str resource: type of generator to consider.
        :return: (*list*) -- plant identification number of all the \ 
            generators located in zone and using resource.
        """
        plant_id = []
        if zone == self.interconnect:
            try:
                plant_id = self.grid.genbus.groupby('type').get_group(
                    resource).index.values.tolist()
            except KeyError:
                pass
        elif zone == 'California':
            ca = ['Bay Area', 'Central California', 'Northern California',
                  'Southeast California', 'Southwest California']
            for load_zone in ca:
                try:
                    plant_id += self.grid.genbus.groupby(
                        ['ZoneName', 'type']).get_group(
                        (load_zone, resource)).index.values.tolist()
                except KeyError:
                    pass
        else:
            try:
                plant_id = self.grid.genbus.groupby(
                    ['ZoneName', 'type']).get_group(
                    (zone, resource)).index.values.tolist()
            except KeyError:
                pass

        return plant_id

    def set_hydro(self, zones=None, plant_id=None):
        """Consign changes relative to hydro plants capacity.

        :param float factor: increase/decrease in capacity.
        :param dict zones: geographical zones. The key(s) is (are) the \ 
            zone(s) and the value is the factor indicating the desired \ 
            increase/decrease in capacity of all the hydro plants in the zone.  
        :param dict plant_id: identification numbers of hydro plants. The \ 
            key(s) is (are) the id of the hydro plant(s) and the value is \ 
            the factor indicated the desired increase/decrease in capacity \ 
            of the hydro plant(s).
        """
        if bool(zones) ^ bool(plant_id) is False:
            print("Set either <zones> or <plant_id>. Return.")
            return
        elif zones is not None:
            self._check_zones(list(zones.keys()))
            self.table['hydro'] = {}
            for z in zones.keys():
                plant_id_zone = self._get_plant_id(z, 'hydro')
                if len(plant_id_zone) == 0:
                    print("No hydro plants in %s" % z)
                else:
                    for i in plant_id_zone:
                        self.table['hydro'][i] = zones[z]
        else:
            plant_id_interconnect = set(self.grid.genbus.groupby(
                                        'type').get_group('hydro').index)
            diff = set(plant_id.keys()).difference(plant_id_interconnect)
            if len(diff) != 0:
                print("No hydro plant(s) with the following id:")
                for i in list(diff):
                    print(i)
                return        
            else:
                self.table['hydro'] = {}
                for i in plant_id.keys():
                    self.table['hydro'][i] = plant_id[i]
        n_plants = len(self.table['hydro'])
        if n_plants > 0:
            print("%d hydro plants consigned" % n_plants)
        else:
            self.table.pop('hydro')        

    def set_demand(self, zones):
        """Consign changes relative to zones.

        :param dict zones: geographical zones. The key(s) is (are) the \ 
            zone(s) and the value is a factor indicating the desired \ 
            increase/decrease of load.
        """
        self._check_zones(list(zones.keys()))
        self.table['demand'] = {}
        for z in zones.keys():
            self.table['demand'][z] = zones[z]
        return self.table
