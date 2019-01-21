import pandas as pd

from powersimdata.input.grid import Grid


class Change():
    """Enclose changes that need to be applied to the original grid as well \ 
        as to the original demand, hydro, solar and wind profiles.

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
            print("%s is incorrect. Possible interconnect are: %s" % possible)
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


    def set_hydro(self, factor, zones=None, plant_id=None):
        """Modify caoacity of hydro plants

        :param float factor: increase/decrease in capacity.
        :param list zones: geographical zones.
        :param list plant_id: identification numbers of hydro plants.
        """
        if bool(zones) ^ bool(plant_id) == False:
            print("Set either <zones> or <plant_id>. Return.")
            return
        elif zones is not None:
            self._check_zones(zones)
            plant_id = []
            for z in zones:
                current_id = self._get_plant_id(z, 'hydro')
                plant_id += current_id
                if len(current_id) == 0:
                    print("No hydro plants in %s" % z)
            print("%d hydro plants will be modified" % len(plant_id))
        else:
            plant_id_interconnect = set(self.grid.genbus.groupby(
                                        'type').get_group('hydro').index)
            diff = set(plant_id).difference(plant_id_interconnect)
            if len(diff) != 0:
                print("The following identification number(s) are wrong:")
                for i in list(diff):
                    print(i)
                return
        self.table['hydro'] = {}
        self.table['hydro']['factor'] = factor
        self.table['hydro']['id'] = plant_id
