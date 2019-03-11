import os
import pickle
from pathlib import Path

import pandas as pd

from powersimdata.input.grid import Grid
from postreise.process.transferdata import PushData


class Change():
    """Create change table for changes that need to be applied to the \
        original grid as well as to the original demand, hydro, solar and \
        wind profiles. A pickle file enclosing the change table in form of a \
        dictionary will be created and transfered on the server. Keys are \
        *'branch'*, *'demand'*, *'hydro'*, *'solar'* and *'wind'*. If a key \
        is missing in the dictionary, then no changes will be applied. The \
        data structure is given below:

        * *'branch'*: \
            value is a dictionnary, which has branch id as key and a \
            factor indicating the desired increase/decrease of capacity of \
            the line (1.2 would correspond to a 20% increase while 0.95 \
            would be a 5% decrease).
        * *'demand'*: \
            value is a dictionnary, which has load zones as keys and a \
            factor indicating the desired increase/decrease of load in zone \
            (1.2 would correspond to a 20% increase while 0.95 would be a 5% \
            decrease).
        * *'hydro'*, *'solar'* and *'wind'*: \
            value is a dictionary, which has the plant id as key and a \
            factor indicating the desired increase/decrease of capacity of \
            the *'hydro'*/*'solar'*/*'wind'* plant (1.2 would correspond to \
            a 20% increase while 0.95 would be a 5% decrease).

    :param str name: name of scenario.
    :param list interconnect: interconnect name(s).
    """

    def __init__(self, name, interconnect):
        """Constructor.

        """
        self.name = name
        if isinstance(interconnect, str):
            self.interconnect = [interconnect]
        else:
            self.interconnect = interconnect

        # Set attribute
        self.grid = Grid(self.interconnect)
        self.table = {}
        self.name2id = {}
        for k, v in self.grid.zone.items():
            try:
                self.name2id[v]
                self.name2id[v].append(k)
            except KeyError:
                self.name2id[v] = [k]

    def _set_interconnect(self, interconnect):
        """Checks interconnect.

        :param list interconnect: interconnect name(s).
        :raises TypeError: if parameter has wrong type.
        :raises NameError: if interconnect does not exist.
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
                raise NameError("Interconnect not available. Choose from %s" %
                                " / ".join(possible))

        self.interconnect = test

    @staticmethod
    def _check_resource(resource):
        """Checks resource.

        :param str resources: type of generator.
        :raises NameError: if resource cannot be changed.
        """
        possible = ['hydro', 'solar', 'wind']
        if resource not in possible:
            print("Choose one of:")
            for p in possible:
                print(p)
            raise NameError('Invalid resource')

    def _check_zone(self, zone):
        """Checks load zones.

        :param list zone: geographical zones.
        :raise NameError: if zone(s) do(es) not exist.
        """
        possible = list(self.grid.plant.zone_name.unique())
        for z in zone:
            if z not in possible:
                print("Possible zones are:")
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
        try:
            plant_id = self.grid.plant.groupby(
                ['zone_name', 'type']).get_group(
                (zone, resource)).index.values.tolist()
        except KeyError:
            pass

        return plant_id

    def set_plant_capacity(self, resource, zone=None, plant_id=None):
        """Consign plant capacity scaling.

        :param str resource: type of generator to consider.
        :param dict zone: geographical zones. The key(s) is (are) the \
            zone(s) and the associated value is the scaling factor for the \
            increase/decrease in capacity of all the generators in the zone \
            of specified type.
        :param dict plant_id: identification numbers of plants. The key(s) \
            is (are) the id of the plant(s) and the associated value is the \
            scaling factor for the increase/decrease in capacity of the \
            generator.
        """
        self._check_resource(resource)
        if bool(zone) or bool(plant_id) is True:
            self.table[resource] = {}
            if zone is not None:
                try:
                    self._check_zone(list(zone.keys()))
                except:
                    self.table.pop(resource)
                    return
                self.table[resource]['zone_id'] = {}
                for z in zone.keys():
                    if len(self._get_plant_id(z, resource)) == 0:
                        print("No %s plants in %s." % (resource, z))
                    else:
                        for i in self.name2id[z]:
                            self.table[resource]['zone_id'][i] = zone[z]
            if plant_id is not None:
                plant_id_interconnect = set(self.grid.plant.groupby(
                    'type').get_group(resource).index)
                diff = set(plant_id.keys()).difference(plant_id_interconnect)
                if len(diff) != 0:
                    print("No %s plant(s) with the following id:" % resource)
                    for i in list(diff):
                        print(i)
                    self.table.pop(resource)
                    return
                else:
                    self.table[resource]['plant_id'] = {}
                    for i in plant_id.keys():
                        self.table[resource]['plant_id'][i] = plant_id[i]
        else:
            print("<zone> and/or <plant_id> must be set. Return.")
            return

    def set_branch_capacity(self, zone=None, branch_id=None):
        """Consign branch capacity scaling.

        :param dict zone: geographical zones. The key(s) is (are) the \
            zone(s) and the associated value is the scaling factor for the \
            increase/decrease in capacity of all the branches in the zone. \
            Only lines that have both ends in zone are considered.
        :param dict branch_id: identification numbers of branches. The \
            key(s) is (are) the id of the line(s) and the associated value \
            is the scaling factor for the increase/decrease in capacity of \
            the line(s).
        """
        if bool(zone) or bool(plant_id) is True:
            self.table['branch'] = {}
            if zone is not None:
                try:
                    self._check_zone(list(zone.keys()))
                except:
                    self.table.pop('branch')
                    return
                self.table['branch']['zone_id'] = {}
                for z in zone.keys():
                    for i in self.name2id[z]:
                        self.table['branch']['zone_id'][i] = zone[z]
            if branch_id is not None:
                branch_id_interconnect = set(self.grid.branch.index)
                diff = set(branch_id.keys()).difference(branch_id_interconnect)
                if len(diff) != 0:
                    print("No branch with the following id:")
                    for i in list(diff):
                        print(i)
                    self.table.pop('branch')
                    return
                else:
                    self.table['branch']['branch_id'] = {}
                    for i in branch_id.keys():
                        self.table['branch']['branch_id'][i] = branch_id[i]
        else:
            print("<zone> and/or <branch_id> must be set. Return.")
            return

    def set_demand(self, zone=None, zone_id=None):
        """Consign load scaling.

        :param dict zone: geographical zones. The key(s) is (are) the \
            zone(s) and the value is the scaling factor for the \
            increase/decrease in load.
        :param dict zone_id: identification numbers of zones. The \
            key(s) is (are) the id of the zone(s) and the associated value \
            is the scaling factor for the increase/decrease in load.
        """
        if bool(zone) or bool(plant_id) is True:
            self.table['demand'] = {}
            if zone is not None:
                try:
                    self._check_zone(list(zone.keys()))
                except:
                    self.table.pop('demand')
                    return
                self.table['demand']['zone_id'] = {}
                for z in zone.keys():
                    for i in self.name2id[z]:
                        self.table['demand']['zone_id'][i] = zone[z]
            if zone_id is not None:
                zone_id_interconnect = set(self.grid.zone.keys())
                diff = set(zone_id.keys()).difference(zone_id_interconnect)
                if len(diff) != 0:
                    print("No zone with the following id:")
                    for i in list(diff):
                        print(i)
                    self.table.pop('demand')
                    return
                else:
                    self.table['demand']['zone_id'] = {}
                    for i in zone_id.keys():
                        self.table['demand']['zone_id'][i] = zone_id[i]
        else:
            print("<zone> and/or <zone_id> must be set. Return.")
            return

    def write(self, local_dir=None):
        """Saves change table to disk..

        :param str local_dir: define local folder location to save data. If \
            not defined, the change table will be saved in *'scenario_data'* \
            folder in home directory.
        """
        if not local_dir:
            home_dir = str(Path.home())
            local_dir = os.path.join(home_dir, 'scenario_data', '')
        print('Local directory is %s' % local_dir)
        if os.path.isdir(local_dir) is False:
            os.makedirs(local_dir)
        file_name = os.path.join(local_dir, self.name + "_ct.pkl")
        if os.path.isfile(file_name) is False:
            print("Write %s." % file_name)
            pickle.dump(self.table, open(file_name, "wb"))
        else:
            print("%s already exists. Return" % file_name)
            return

    def push(self, local_dir=None):
        """Transfers file to server.

        :param str local_dir: define local folder location. If not defined, \
            it is assumed that the change table is located in the \
            *'scenario_data'* folder in the home directory.
        """
        if not local_dir:
            home_dir = str(Path.home())
            local_dir = os.path.join(home_dir, 'scenario_data', '')
        print('Local directory is %s' % local_dir)
        TD = PushData(local_dir)
        TD.upload(self.name, 'ct')
