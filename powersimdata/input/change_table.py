import os
import pickle

from powersimdata.input.design_transmission import (
    scale_congested_mesh_branches, scale_renewable_stubs)
from powersimdata.input.grid import Grid
from postreise.process import const


_resources = ('coal', 'dfo', 'geothermal', 'ng', 'nuclear',
              'hydro', 'solar', 'wind', 'biomass', 'other')


class ChangeTable(object):
    """Create change table for changes that need to be applied to the original
        grid as well as to the original demand, hydro, solar and wind profiles.
        A pickle file enclosing the change table in form of a dictionary can be
        created and transferred on the server. Keys are *'demand'*, *'branch'*,
        *'biomass'*, *'coal'*, *'dfo'*, *'geothermal'*, *'ng'*, *'nuclear'*,
        *'hydro'*, *'solar'*, *'wind'*, *'other'*, and *'storage'*.
        If a key is missing in the dictionary, then no changes will be applied.
        The data structure is given below:

        * *'demand'*:
            value is a dictionary. The latter has *'zone_id'* as keys and a
            factor indicating the desired increase/decrease of load in zone
            (1.2 would correspond to a 20% increase while 0.95 would be a 5%
            decrease) as value.
        * *'branch'*:
            value is a dictionary. The latter has *'branch_id'* and/or
            *'zone_id'* as keys. The *'branch_id'* dictionary has the branch
            ids as keys while the *'zone_id'* dictionary has the zone ids as
            keys. The value of those dictionaries is a factor indicating the
            desired increase/decrease of capacity of the line or the lines in
            the zone (1.2 would correspond to a 20% increase while 0.95 would
            be a 5% decrease).
        * *'biomass'*, *'coal'*, *'dfo'*, *'geothermal'*, *'ng'*, *'nuclear'*,
            *'hydro'*, *'solar'*, *'wind'*, and *'other'*:
            value is a dictionary. The latter has *'plant_id'* and/or
            *'zone_id'* as keys. The *'plant_id'* dictionary has the plant ids
            as keys while the *'zone_id'* dictionary has the zone ids as keys.
            The value of those dictionaries is a factor indicating the desired
            increase/decrease of capacity of the plant or plants in the zone
            (1.2 would correspond to a 20% increase while 0.95 would be a 5%
            decrease).
        * *'storage'*:
            value is a dictionary. The latter has *'bus_id'* as keys and the
             capacity of storage (in MW) to add as value.

        :param list interconnect: interconnect name(s).
    """

    def __init__(self, interconnect):
        """Constructor.

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
        possible = _resources
        if resource not in possible:
            print("-----------------------")
            print("Possible Generator type")
            print("-----------------------")
            for p in possible:
                print(p)
            raise ValueError('Invalid resource: %s' % resource)

    def _check_zone(self, zone_name):
        """Checks load zones.

        :param list zone_name: load zones.
        :raise ValueError: if zone(s) do(es) not exist.
        """
        possible = list(self.grid.plant.zone_name.unique())
        for z in zone_name:
            if z not in possible:
                print("--------------")
                print("Possible zones")
                print("--------------")
                for p in possible:
                    print(p)
                raise ValueError('Invalid load zone(s): %s' %
                                 " | ".join(zone_name))

    def _get_plant_id(self, zone_name, resource):
        """Returns the plant identification number of all the generators
            located in specified zone and fueled by specified resource.

        :param str zone_name: load zone to consider.
        :param str resource: type of generator to consider.
        :return: (*list*) -- plant identification number of all the generators
            located in zone and fueled by resource.
        """
        plant_id = []
        try:
            plant_id = self.grid.plant.groupby(
                ['zone_name', 'type']).get_group(
                (zone_name, resource)).index.values.tolist()
        except KeyError:
            pass

        return plant_id

    def clear(self, which=None):
        """Clear all or part of the change table.

        :param set which: set of strings of what to clear from self.ct
        """
        if which is None:
            which = {'all'}
        if isinstance(which, str):
            which = {which}
        allowed = {'all', 'branch', 'dcline', 'plant', 'storage'}
        if not which <= allowed:
            raise ValueError('which must contain only: ' + ' | '.join(allowed))
        if 'all' in which:
            self.ct = {}
            return
        for key in ('branch', 'dcline', 'storage'):
            if key in which:
                del self.ct[key]
        if 'plant' in which:
            for r in _resources:
                if r in self.ct:
                    del self.ct[r]

    def scale_plant_capacity(self, resource, zone_name=None, plant_id=None):
        """Sets plant capacity scaling factor in change table.

        :param str resource: type of generator to consider.
        :param dict zone_name: load zones. The key(s) is (are) the name of the
            load zone(s) and the associated value is the scaling factor for the
            increase/decrease in capacity of all the generators fueled by
            specified resource in the load zone.
        :param dict plant_id: identification numbers of plants. The key(s) is
            (are) the id of the plant(s) and the associated value is the
            scaling factor for the increase/decrease in capacity of the
            generator.
        """
        self._check_resource(resource)
        if bool(zone_name) or bool(plant_id) is True:
            if resource not in self.ct:
                self.ct[resource] = {}
            if zone_name is not None:
                try:
                    self._check_zone(list(zone_name.keys()))
                except ValueError:
                    self.ct.pop(resource)
                    return
                if 'zone_id' not in self.ct[resource]:
                    self.ct[resource]['zone_id'] = {}
                for z in zone_name.keys():
                    if len(self._get_plant_id(z, resource)) == 0:
                        print("No %s plants in %s." % (resource, z))
                    else:
                        self.ct[resource]['zone_id'][
                            self.grid.zone2id[z]] = zone_name[z]
                if len(self.ct[resource]['zone_id']) == 0:
                    self.ct.pop(resource)
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
                    if 'plant_id' not in self.ct[resource]:
                        self.ct[resource]['plant_id'] = {}
                    for i in plant_id.keys():
                        self.ct[resource]['plant_id'][i] = plant_id[i]
        else:
            print("<zone> and/or <plant_id> must be set. Return.")
            return

    def scale_branch_capacity(self, zone_name=None, branch_id=None):
        """Sets branch capacity scaling factor in change table.

        :param dict zone_name: load zones. The key(s) is (are) the name of the
            load zone(s) and the associated value is the scaling factor for
            the increase/decrease in capacity of all the branches in the load
            zone. Only lines that have both ends in zone are considered.
        :param dict branch_id: identification numbers of branches. The key(s)
            is (are) the id of the line(s) and the associated value is the
            scaling factor for the increase/decrease in capacity of the line(s).
        """
        if bool(zone_name) or bool(branch_id) is True:
            if 'branch' not in self.ct:
                self.ct['branch'] = {}
            if zone_name is not None:
                try:
                    self._check_zone(list(zone_name.keys()))
                except ValueError:
                    self.ct.pop('branch')
                    return
                if 'zone_id' not in self.ct['branch']:
                    self.ct['branch']['zone_id'] = {}
                for z in zone_name.keys():
                    self.ct['branch']['zone_id'][
                        self.grid.zone2id[z]] = zone_name[z]
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
                    if 'branch_id' not in self.ct['branch']:
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
        if 'dcline' not in self.ct:
            self.ct['dcline'] = {}
        diff = set(dcline_id.keys()).difference(set(self.grid.dcline.index))
        if len(diff) != 0:
            print("No dc line with the following id:")
            for i in list(diff):
                print(i)
            self.ct.pop('dcline')
            return
        else:
            if 'dcline_id' not in self.ct['dcline']:
                self.ct['dcline']['dcline_id'] = {}
            for i in dcline_id.keys():
                self.ct['dcline']['dcline_id'][i] = dcline_id[i]

    def scale_demand(self, zone_name=None, zone_id=None):
        """Sets load scaling factor in change table.

        :param dict zone_name: load zones. The key(s) is (are) the name of the
            load zone(s) and the value is the scaling factor for the
            increase/decrease in load.
        :param dict zone_id: identification numbers of the load zones. The
            key(s) is (are) the id of the zone(s) and the associated value is
            the scaling factor for the increase/decrease in load.
        """
        if bool(zone_name) or bool(zone_id) is True:
            if 'demand' not in self.ct:
                self.ct['demand'] = {}
            if 'zone_id' not in self.ct['demand']:
                self.ct['demand']['zone_id'] = {}
            if zone_name is not None:
                try:
                    self._check_zone(list(zone_name.keys()))
                except ValueError:
                    self.ct.pop('demand')
                    return
                for z in zone_name.keys():
                    self.ct['demand']['zone_id'][
                        self.grid.zone2id[z]] = zone_name[z]
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
                    for i in zone_id.keys():
                        self.ct['demand']['zone_id'][i] = zone_id[i]
        else:
            print("<zone> and/or <zone_id> must be set. Return.")
            return

    def scale_renewable_stubs(self, **kwargs):
        """Scales undersized stub branches connected to renewable generators.
        Optional kwargs as documented in powersimdata.input.design_transmission
        """
        scale_renewable_stubs(self, **kwargs)
    
    def scale_congested_mesh_branches(self, ref_scenario, **kwargs):
        """Scales congested branches based on previous scenario results.
        :param powersimdata.scenario.scenario.Scenario ref_scenario: the
            reference scenario to be used in determining branch scaling.
        Optional kwargs as documented in powersimdata.input.design_transmission
        """
        scale_congested_mesh_branches(self, ref_scenario, **kwargs)

    def add_storage_capacity(self, bus_id):
        """Sets storage parameters in change table.

        :param dict bus_id: key(s) for the id of bus(es), value(s) is (are)
            capacity of the energy storage system in MW.
        """
        if 'storage' not in self.ct:
            self.ct['storage'] = {}

        diff = set(bus_id.keys()).difference(set(self.grid.bus.index))
        if len(diff) != 0:
            print("No bus with the following id:")
            for i in list(diff):
                print(i)
            self.ct.pop('storage')
            return
        else:
            if 'bus_id' not in self.ct['storage']:
                self.ct['storage']['bus_id'] = {}
            for i in bus_id.keys():
                self.ct['storage']['bus_id'][i] = bus_id[i]

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
