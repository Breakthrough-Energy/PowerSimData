import os
import pickle

from powersimdata.input.grid import Grid
from postreise.process import const


class ChangeTable(object):
    """Create change table for changes that need to be applied to the original
        grid as well as to the original demand, hydro, solar and wind profiles.
        A pickle file enclosing the change table in form of a dictionary can be
        created and transferred on the server. Keys are *'branch'*, *'demand'*,
        *'hydro'*, *'solar'* and *'wind'*. If a key is missing in the
        dictionary, then no changes will be applied. The data structure is
        given below:

        * *'branch'*:
            value is a dictionary, which has branch id as key and a factor
            indicating the desired increase/decrease of capacity of the line
            (1.2 would correspond to a 20% increase while 0.95 would be a 5%
            decrease).
        * *'demand'*:
            value is a dictionary, which has load zones as keys and a factor
            indicating the desired increase/decrease of load in zone (1.2 would
            correspond to a 20% increase while 0.95 would be a 5% decrease).
        * *'coal'*, *'ng'*, *'nuclear'*, *'hydro'*, *'solar'* and *'wind'*:
            value is a dictionary, which has the plant id as key and a factor
            indicating the desired increase/decrease of capacity of the
            *'hydro'*/*'solar'*/*'wind'* plant (1.2 would correspond to a 20%
            increase while 0.95 would be a 5% decrease).
    """

    def __init__(self, interconnect):
        """Constructor.

        :param list interconnect: interconnect name(s).
        """
        if isinstance(interconnect, str):
            self.grid = Grid([interconnect])
        else:
            self.grid = Grid(interconnect)

        # Set attribute
        self.ct = {}

    @staticmethod
    def _check_resource(resource):
        """Checks resource.

        :param str resource: type of generator.
        :raises ValueError: if resource cannot be changed.
        """
        possible = ['coal', 'ng', 'nuclear', 'hydro', 'solar', 'wind']
        if resource not in possible:
            print("-----------------------")
            print("Possible Generator type")
            print("-----------------------")
            for p in possible:
                print(p)
            raise ValueError('Invalid resource: %s' % resource)

    def _check_zone(self, zone):
        """Checks load zones.

        :param list zone: geographical zones.
        :raise ValueError: if zone(s) do(es) not exist.
        """
        possible = list(self.grid.plant.zone_name.unique())
        for z in zone:
            if z not in possible:
                print("--------------")
                print("Possible zones")
                print("--------------")
                for p in possible:
                    print(p)
                raise ValueError('Invalid zone(s): %s' % " | ".join(zone))

    def _get_plant_id(self, zone, resource):
        """Returns the plant identification number of all the generators
            located in one zone and using one specific resource.

        :param str zone: zone to consider.
        :param str resource: type of generator to consider.
        :return: (*list*) -- plant identification number of all the generators
            located in zone and using resource.
        """
        plant_id = []
        try:
            plant_id = self.grid.plant.groupby(
                ['zone_name', 'type']).get_group(
                (zone, resource)).index.values.tolist()
        except KeyError:
            pass

        return plant_id

    def scale_plant_capacity(self, resource, zone=None, plant_id=None):
        """Sets plant capacity scaling factor in change table.

        :param str resource: type of generator to consider.
        :param dict zone: geographical zones. The key(s) is (are) the zone(s)
            and the associated value is the scaling factor for the
            increase/decrease in capacity of all the generators in the zone of
            specified type.
        :param dict plant_id: identification numbers of plants. The key(s) is
            (are) the id of the plant(s) and the associated value is the
            scaling factor for the increase/decrease in capacity of the
            generator.
        """
        self._check_resource(resource)
        if bool(zone) or bool(plant_id) is True:
            self.ct[resource] = {}
            if zone is not None:
                try:
                    self._check_zone(list(zone.keys()))
                except ValueError:
                    self.ct.pop(resource)
                    return
                self.ct[resource]['zone_id'] = {}
                for z in zone.keys():
                    if len(self._get_plant_id(z, resource)) == 0:
                        print("No %s plants in %s." % (resource, z))
                    else:
                        for i in self.grid.zone2id[z]:
                            self.ct[resource]['zone_id'][i] = zone[z]
            if plant_id is not None:
                plant_id_interconnect = set(self.grid.plant.groupby(
                    'type').get_group(resource).index)
                diff = set(plant_id.keys()).difference(plant_id_interconnect)
                if len(diff) != 0:
                    print("No %s plant(s) with the following id:" % resource)
                    for i in list(diff):
                        print(i)
                    self.ct.pop(resource)
                    return
                else:
                    self.ct[resource]['plant_id'] = {}
                    for i in plant_id.keys():
                        self.ct[resource]['plant_id'][i] = plant_id[i]
        else:
            print("<zone> and/or <plant_id> must be set. Return.")
            return

    def scale_branch_capacity(self, zone=None, branch_id=None):
        """Sets branch capacity scaling factor in change table.

        :param dict zone: geographical zones. The key(s) is (are) the zone(s)
            and the associated value is the scaling factor for the
            increase/decrease in capacity of all the branches in the zone. Only
            lines that have both ends in zone are considered.
        :param dict branch_id: identification numbers of branches. The key(s)
            is (are) the id of the line(s) and the associated value is the
            scaling factor for the increase/decrease in capacity of the line(s).
        """
        if bool(zone) or bool(branch_id) is True:
            self.ct['branch'] = {}
            if zone is not None:
                try:
                    self._check_zone(list(zone.keys()))
                except ValueError:
                    self.ct.pop('branch')
                    return
                self.ct['branch']['zone_id'] = {}
                for z in zone.keys():
                    for i in self.grid.zone2id[z]:
                        self.ct['branch']['zone_id'][i] = zone[z]
            if branch_id is not None:
                branch_id_interconnect = set(self.grid.branch.index)
                diff = set(branch_id.keys()).difference(branch_id_interconnect)
                if len(diff) != 0:
                    print("No branch with the following id:")
                    for i in list(diff):
                        print(i)
                    self.ct.pop('branch')
                    return
                else:
                    self.ct['branch']['branch_id'] = {}
                    for i in branch_id.keys():
                        self.ct['branch']['branch_id'][i] = branch_id[i]
        else:
            print("<zone> and/or <branch_id> must be set. Return.")
            return

    def scale_dcline_capacity(self, dcline_id):
        """Sets DC line capacity scaling factor in change table.

        :param dict dcline_id: identification numbers of dc line. The key(s) is
            (are) the id of the line(s) and the associated value is the scaling
            factor for the increase/decrease in capacity of the line(s).
        """
        self.ct['dcline'] = {}
        self.ct['dcline']['dcline_id'] = {}
        diff = set(dcline_id.keys()).difference(set(self.grid.dcline.index))
        if len(diff) != 0:
            print("No dc line with the following id:")
            for i in list(diff):
                print(i)
            self.ct.pop('dcline')
            return
        else:
            self.ct['dcline']['dcline_id'] = {}
            for i in dcline_id.keys():
                self.ct['dcline']['dcline_id'][i] = dcline_id[i]

    def scale_demand(self, zone=None, zone_id=None):
        """Sets load scaling factor in change table.

        :param dict zone: geographical zones. The key(s) is (are) the zone(s)
            and the value is the scaling factor for the increase/decrease in
            load.
        :param dict zone_id: identification numbers of zones. The key(s) is
            (are) the id of the zone(s) and the associated value is the scaling
            factor for the increase/decrease in load.
        """
        if bool(zone) or bool(zone_id) is True:
            self.ct['demand'] = {}
            if zone is not None:
                try:
                    self._check_zone(list(zone.keys()))
                except ValueError:
                    self.ct.pop('demand')
                    return
                self.ct['demand']['zone_id'] = {}
                for z in zone.keys():
                    for i in self.grid.zone2id[z]:
                        self.ct['demand']['zone_id'][i] = zone[z]
            if zone_id is not None:
                zone_id_interconnect = set(self.grid.id2zone.keys())
                diff = set(zone_id.keys()).difference(zone_id_interconnect)
                if len(diff) != 0:
                    print("No zone with the following id:")
                    for i in list(diff):
                        print(i)
                    self.ct.pop('demand')
                    return
                else:
                    self.ct['demand']['zone_id'] = {}
                    for i in zone_id.keys():
                        self.ct['demand']['zone_id'][i] = zone_id[i]
        else:
            print("<zone> and/or <zone_id> must be set. Return.")
            return

    def write(self, scenario_id):
        """Saves change table to disk.

        :param str scenario_id: scenario index.
        :raises IOError: if file already exists on local machine.
        """
        if not os.path.exists(const.LOCAL_DIR):
            os.makedirs(const.LOCAL_DIR)

        file_name = os.path.join(const.LOCAL_DIR, scenario_id + "_ct.pkl")
        if os.path.isfile(file_name) is False:
            print("Writing %s" % file_name)
            pickle.dump(self.ct, open(file_name, "wb"))
        else:
            raise IOError("%s already exists" % file_name)
