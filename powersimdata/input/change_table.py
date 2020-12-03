import os
import pickle

from powersimdata.design.transmission.upgrade import (
    scale_congested_mesh_branches,
    scale_renewable_stubs,
)
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.utility import server_setup
from powersimdata.utility.distance import find_closest_neighbor, haversine

_resources = (
    "coal",
    "dfo",
    "geothermal",
    "ng",
    "nuclear",
    "hydro",
    "solar",
    "wind",
    "wind_offshore",
    "biomass",
    "other",
)

_renewable_resource = {"hydro", "solar", "wind", "wind_offshore"}


class ChangeTable(object):
    """Create change table for changes that need to be applied to the original
    grid as well as to the original demand, hydro, solar and wind profiles.
    A pickle file enclosing the change table in form of a dictionary can be
    created and transferred on the server. Keys are *'demand'*, *'branch'*, *'dcline'*,
    '*new_branch*', *'new_dcline'*, *'new_plant'*, *'storage'*,
    *'[resource]'*, *'[resource]_cost'*, and *'[resource]_pmin'*,; where 'resource'
    is one of: {*'biomass'*, *'coal'*, *'dfo'*, *'geothermal'*, *'ng'*, *'nuclear'*,
    *'hydro'*, *'solar'*, *'wind'*, *'wind_offshore'*, *'other'*}.
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
    * *'[resource]'*:
        value is a dictionary. The latter has *'plant_id'* and/or
        *'zone_id'* as keys. The *'plant_id'* dictionary has the plant ids
        as keys while the *'zone_id'* dictionary has the zone ids as keys.
        The value of those dictionaries is a factor indicating the desired
        increase/decrease of capacity of the plant or plants in the zone fueled by
        *'[resource]'* (1.2 would correspond to a 20% increase while 0.95 would be
        a 5% decrease).
    * *'[resource]_cost'*:
        value is a dictionary. The latter has *'plant_id'* and/or
        *'zone_id'* as keys. The *'plant_id'* dictionary has the plant ids
        as keys while the *'zone_id'* dictionary has the zone ids as keys.
        The value of those dictionaries is a factor indicating the desired
        increase/decrease of cost of the plant or plants in the zone fueled by
        *'[resource]'* (1.2 would correspond to a 20% increase while 0.95 would be
        a 5% decrease).
    * *'[resource]_pmin*:
        value is a dictionary. The latter has *'plant_id'* and/or
        *'zone_id'* as keys. The *'plant_id'* dictionary has the plant ids
        as keys while the *'zone_id'* dictionary has the zone ids as keys.
        The value of those dictionaries is a factor indicating the desired
        increase/decrease of minimum generation of the plant or plants in the zone
        fueled by *'[resource]'* (1.2 would correspond to a 20% increase while
        0.95 would be a 5% decrease).
    * *'dcline'*:
        value is a dictionary. The latter has *'dcline_id'* as keys and
        the and the scaling factor for the increase/decrease in capacity
        of the line as value.
    * *'storage'*:
        value is a dictionary. The latter has *'bus_id'* as keys and the
        capacity of storage (in MW) to add as value.
    * *'new_dcline'*:
        value is a list. Each entry in this list is a dictionary enclosing
        all the information needed to add a new dcline to the grid. The
        keys in the dictionary are: *'capacity'*, *'from_bus_id'* and
        *'to_bus_id'* with values giving the capacity of the HVDC line and
        the bus id at each end of the line.
    * *'new_branch'*:
        value is a list. Each entry in this list is a dictionary enclosing
        all the information needed to add a new branch to the grid. The
        keys in the dictionary are: *'capacity'*, *'from_bus_id'* and
        *'to_bus_id'* with values giving the capacity of the line and
        the bus id at each end of the line.
    * *'new_plant'*:
        value is a list. Each entry in this list is a dictionary enclosing
        all the information needed to add a new generator to the grid. The
        keys in the dictionary are *'type'*, *'bus_id'*, *'Pmax'* for
        renewable generators and *'type'*, *'bus_id'*, *'Pmax'*, *'c0'*,
        *'c1'*, *'c2'* for thermal generators. An optional *'Pmin'* can be
        passed for both renewable and thermal generators. The values give
        the fuel type, the identification number of the bus, the maximum
        capacity of the generator, the coefficients of the cost curve
        (polynomials) and optionally the minimum capacity of the generator.
    """

    def __init__(self, grid):
        """Constructor.

        :param powersimdata.input.grid.Grid grid: a Grid object
        """
        self.grid = grid
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
            raise ValueError("Invalid resource: %s" % resource)

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
                raise ValueError("Invalid load zone(s): %s" % " | ".join(zone_name))

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
            plant_id = (
                self.grid.plant.groupby(["zone_name", "type"])
                .get_group((zone_name, resource))
                .index.values.tolist()
            )
        except KeyError:
            pass

        return plant_id

    def clear(self, which=None):
        """Clear all or part of the change table.

        :param str/set which: str or set of strings of what to clear from self.ct
            If None or "all", everything is cleared.
        """
        # Input validation
        allowed = {"all", "branch", "dcline", "demand", "plant", "storage"}
        if which is None:
            which = {"all"}
        if isinstance(which, str):
            which = {which}
        if not which <= allowed:
            raise ValueError("which must contain only: " + " | ".join(allowed))
        # Clear all
        if "all" in which:
            self.ct.clear()
            return
        # Clear only top-level keys specified in which
        for key in {"demand", "storage"}:
            if key in which:
                del self.ct[key]
        # Clear multiple keys for each entry in which
        for line_type in {"branch", "dcline"}:
            if line_type in which:
                for prefix in {"", "new_"}:
                    key = prefix + line_type
                    if key in self.ct:
                        del self.ct[key]
        if "plant" in which:
            if "new_plant" in self.ct:
                del self.ct["new_plant"]
            for r in _resources:
                for suffix in {"", "_cost", "_pmin"}:
                    key = r + suffix
                    if key in self.ct:
                        del self.ct[key]

    def _add_plant_entries(self, resource, ct_key, zone_name=None, plant_id=None):
        """Sets plant entries in change table.

        :param str resource: type of generator to consider.
        :param str ct_key: top-level key to add to the change table.
        :param dict zone_name: load zones. The key(s) is (are) the name of the
            load zone(s) and the associated value is the entry for all the generators
            fueled by specified resource in the load zone.
        :param dict plant_id: identification numbers of plants. The key(s) is
            (are) the id of the plant(s) and the associated value is the entry for
            that generator.
        :raise ValueError: if any values within zone_name or plant_id are negative.
        """
        self._check_resource(resource)
        if bool(zone_name) or bool(plant_id) is True:
            if ct_key not in self.ct:
                self.ct[ct_key] = {}
            if zone_name is not None:
                try:
                    self._check_zone(list(zone_name.keys()))
                except ValueError:
                    self.ct.pop(ct_key)
                    raise
                if not all([v >= 0 for v in zone_name.values()]):
                    raise ValueError(f"All entries for {ct_key} must be non-negative")
                if "zone_id" not in self.ct[ct_key]:
                    self.ct[ct_key]["zone_id"] = {}
                for z in zone_name.keys():
                    if len(self._get_plant_id(z, resource)) == 0:
                        print("No %s plants in %s." % (resource, z))
                    else:
                        zone_id = self.grid.zone2id[z]
                        self.ct[ct_key]["zone_id"][zone_id] = zone_name[z]
                if len(self.ct[ct_key]["zone_id"]) == 0:
                    self.ct.pop(ct_key)
            if plant_id is not None:
                plant_id_interconnect = set(
                    self.grid.plant.groupby("type").get_group(resource).index
                )
                diff = set(plant_id.keys()).difference(plant_id_interconnect)
                if len(diff) != 0:
                    err_msg = f"No {resource} plant(s) with the following id: "
                    err_msg += ", ".join(sorted([str(d) for d in diff]))
                    self.ct.pop(ct_key)
                    raise ValueError(err_msg)
                if not all([v >= 0 for v in plant_id.values()]):
                    raise ValueError(f"All entries for {ct_key} must be non-negative")
                if "plant_id" not in self.ct[ct_key]:
                    self.ct[ct_key]["plant_id"] = {}
                for i in plant_id.keys():
                    self.ct[ct_key]["plant_id"][i] = plant_id[i]
        else:
            raise ValueError("<zone> and/or <plant_id> must be set.")

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
        self._add_plant_entries(resource, resource, zone_name, plant_id)

    def scale_plant_cost(self, resource, zone_name=None, plant_id=None):
        """Sets plant cost scaling factor in change table.

        :param str resource: type of generator to consider.
        :param dict zone_name: load zones. The key(s) is (are) the name of the
            load zone(s) and the associated value is the scaling factor for the
            increase/decrease in cost of all the generators fueled by
            specified resource in the load zone.
        :param dict plant_id: identification numbers of plants. The key(s) is
            (are) the id of the plant(s) and the associated value is the
            scaling factor for the increase/decrease in cost of the
            generator.
        """
        self._add_plant_entries(resource, f"{resource}_cost", zone_name, plant_id)

    def scale_plant_pmin(self, resource, zone_name=None, plant_id=None):
        """Sets plant cost scaling factor in change table.

        :param str resource: type of generator to consider.
        :param dict zone_name: load zones. The key(s) is (are) the name of the
            load zone(s) and the associated value is the scaling factor for the
            minimum generation for all generators fueled by
            specified resource in the load zone.
        :param dict plant_id: identification numbers of plants. The key(s) is
            (are) the id of the plant(s) and the associated value is the
            scaling factor for the minimum generation of the generator.
        """
        self._add_plant_entries(resource, f"{resource}_pmin", zone_name, plant_id)
        # Check for situations where Pmin would be scaled above Pmax
        candidate_grid = TransformGrid(self.grid, self.ct).get_grid()
        pmax_pmin_ratio = candidate_grid.plant.Pmax / candidate_grid.plant.Pmin
        to_be_clipped = pmax_pmin_ratio < 1
        num_clipped = to_be_clipped.sum()
        if num_clipped > 0:
            err_msg = (
                f"{num_clipped} plants would have Pmin > Pmax; "
                "these plants will have Pmin scaling clipped so that Pmin = Pmax"
            )
            print(err_msg)
            # Add by-plant correction factors as necessary
            for plant_id, correction in pmax_pmin_ratio[to_be_clipped].items():
                if "plant_id" not in self.ct[f"{resource}_pmin"]:
                    self.ct[f"{resource}_pmin"]["plant_id"] = {}
                if plant_id in self.ct[f"{resource}_pmin"]["plant_id"]:
                    self.ct[f"{resource}_pmin"]["plant_id"][plant_id] *= correction
                else:
                    self.ct[f"{resource}_pmin"]["plant_id"][plant_id] = correction

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
            if "branch" not in self.ct:
                self.ct["branch"] = {}
            if zone_name is not None:
                try:
                    self._check_zone(list(zone_name.keys()))
                except ValueError:
                    self.ct.pop("branch")
                    return
                if "zone_id" not in self.ct["branch"]:
                    self.ct["branch"]["zone_id"] = {}
                for z in zone_name.keys():
                    self.ct["branch"]["zone_id"][self.grid.zone2id[z]] = zone_name[z]
            if branch_id is not None:
                branch_id_interconnect = set(self.grid.branch.index)
                diff = set(branch_id.keys()).difference(branch_id_interconnect)
                if len(diff) != 0:
                    print("No branch with the following id:")
                    for i in list(diff):
                        print(i)
                    self.ct.pop("branch")
                    return
                else:
                    if "branch_id" not in self.ct["branch"]:
                        self.ct["branch"]["branch_id"] = {}
                    for i in branch_id.keys():
                        self.ct["branch"]["branch_id"][i] = branch_id[i]
        else:
            print("<zone> and/or <branch_id> must be set. Return.")
            return

    def scale_dcline_capacity(self, dcline_id):
        """Sets DC line capacity scaling factor in change table.

        :param dict dcline_id: identification numbers of dc line. The key(s) is
            (are) the id of the line(s) and the associated value is the scaling
            factor for the increase/decrease in capacity of the line(s).
        """
        if "dcline" not in self.ct:
            self.ct["dcline"] = {}
        diff = set(dcline_id.keys()).difference(set(self.grid.dcline.index))
        if len(diff) != 0:
            print("No dc line with the following id:")
            for i in list(diff):
                print(i)
            self.ct.pop("dcline")
            return
        else:
            if "dcline_id" not in self.ct["dcline"]:
                self.ct["dcline"]["dcline_id"] = {}
            for i in dcline_id.keys():
                self.ct["dcline"]["dcline_id"][i] = dcline_id[i]

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
            if "demand" not in self.ct:
                self.ct["demand"] = {}
            if "zone_id" not in self.ct["demand"]:
                self.ct["demand"]["zone_id"] = {}
            if zone_name is not None:
                try:
                    self._check_zone(list(zone_name.keys()))
                except ValueError:
                    self.ct.pop("demand")
                    return
                for z in zone_name.keys():
                    self.ct["demand"]["zone_id"][self.grid.zone2id[z]] = zone_name[z]
            if zone_id is not None:
                zone_id_interconnect = set(self.grid.id2zone.keys())
                diff = set(zone_id.keys()).difference(zone_id_interconnect)
                if len(diff) != 0:
                    print("No zone with the following id:")
                    for i in list(diff):
                        print(i)
                    self.ct.pop("demand")
                    return
                else:
                    for i in zone_id.keys():
                        self.ct["demand"]["zone_id"][i] = zone_id[i]
        else:
            print("<zone> and/or <zone_id> must be set. Return.")
            return

    def scale_renewable_stubs(self, **kwargs):
        """Scales undersized stub branches connected to renewable generators.

        Optional kwargs as documented in the
            :mod:`powersimdata.design.transmission.upgrade` module.
        """
        scale_renewable_stubs(self, **kwargs)

    def scale_congested_mesh_branches(self, ref_scenario, **kwargs):
        """Scales congested branches based on previous scenario results.

        :param powersimdata.scenario.scenario.Scenario ref_scenario: the
            reference scenario to be used in determining branch scaling.

        Optional kwargs as documented in the
            :mod:`powersimdata.design.transmission.upgrade` module.
        """
        scale_congested_mesh_branches(self, ref_scenario, **kwargs)

    def add_storage_capacity(self, bus_id):
        """Sets storage parameters in change table.

        :param dict bus_id: key(s) for the id of bus(es), value(s) is (are)
            capacity of the energy storage system in MW.
        """
        if "storage" not in self.ct:
            self.ct["storage"] = {}

        diff = set(bus_id.keys()).difference(set(self.grid.bus.index))
        if len(diff) != 0:
            print("No bus with the following id:")
            for i in list(diff):
                print(i)
            self.ct.pop("storage")
            return
        else:
            if "bus_id" not in self.ct["storage"]:
                self.ct["storage"]["bus_id"] = {}
            for i in bus_id.keys():
                self.ct["storage"]["bus_id"][i] = bus_id[i]

    def add_dcline(self, info):
        """Adds HVDC line(s).

        :param list info: each entry is a dictionary. The dictionary gathers
            the information needed to create a new dcline.
        """
        if not isinstance(info, list):
            print("Argument enclosing new HVDC line(s) must be a list")
            return

        self._add_line("new_dcline", info)

    def add_branch(self, info):
        """Sets parameters of new branch(es) in change table.

        :param list info: each entry is a dictionary. The dictionary gathers
            the information needed to create a new branch.
        """
        if not isinstance(info, list):
            print("Argument enclosing new AC line(s) must be a list")
            return

        self._add_line("new_branch", info)

    def _add_line(self, key, info):
        """Handles line(s) addition in change table.

        :param str key: key in change table. Either *'new_branch'* or
            *'new_dcline'*
        :param list info: parameters of the line.
        """
        if key not in self.ct:
            self.ct[key] = []

        required_info = ["capacity", "from_bus_id", "to_bus_id"]
        for i, line in enumerate(info):
            if not isinstance(line, dict):
                print("Each entry must be a dictionary")
                self.ct.pop(key)
                return
            elif set(line.keys()) != set(required_info):
                print("Dictionary must have %s as keys" % " | ".join(required_info))
                self.ct.pop(key)
                return
            else:
                start = line["from_bus_id"]
                end = line["to_bus_id"]
                if start not in self.grid.bus.index:
                    print(
                        "No bus with the following id for line #%d: %d" % (i + 1, start)
                    )
                    self.ct.pop(key)
                    return
                elif end not in self.grid.bus.index:
                    print(
                        "No bus with the following id for line #%d: %d" % (i + 1, end)
                    )
                    self.ct.pop(key)
                    return
                elif start == end:
                    print("buses of line #%d must be different" % (i + 1))
                    self.ct.pop(key)
                    return
                elif line["capacity"] < 0:
                    print("capacity of line #%d must be positive" % (i + 1))
                    self.ct.pop(key)
                    return
                elif (
                    key == "new_branch"
                    and self.grid.bus.interconnect[start]
                    != self.grid.bus.interconnect[end]
                ):
                    print("Buses of line #%d must be in same interconnect" % (i + 1))
                    self.ct.pop(key)
                    return

                elif (
                    haversine(
                        (self.grid.bus.lat[start], self.grid.bus.lon[start]),
                        (self.grid.bus.lat[end], self.grid.bus.lon[end]),
                    )
                    == 0
                ):
                    print("Distance between buses of line #%d is 0" % (i + 1))
                    self.ct.pop(key)
                    return

                self.ct[key].append(line)

    def add_plant(self, info):
        """Sets parameters of new generator(s) in change table.

        :param list info: each entry is a dictionary. The dictionary gathers
            the information needed to create a new generator.
        """
        if not isinstance(info, list):
            print("Argument enclosing new plant(s) must be a list")
            return

        if "new_plant" not in self.ct:
            self.ct["new_plant"] = []

        for i, plant in enumerate(info):
            if not isinstance(plant, dict):
                print("Each entry must be a dictionary")
                self.ct.pop("new_plant")
                return
            if "type" not in plant.keys():
                print("Missing key type for plant #%d" % (i + 1))
                self.ct.pop("new_plant")
                return
            else:
                try:
                    self._check_resource(plant["type"])
                except ValueError:
                    self.ct.pop("new_plant")
                    return
            if "bus_id" not in plant.keys():
                print("Missing key bus_id for plant #%d" % (i + 1))
                self.ct.pop("new_plant")
                return
            elif plant["bus_id"] not in self.grid.bus.index:
                print("No bus id %d available for plant #%d" % (plant["bus_id"], i + 1))
                self.ct.pop("new_plant")
                return
            if "Pmax" not in plant.keys():
                print("Missing key Pmax for plant #%d" % (i + 1))
                self.ct.pop("new_plant")
                return
            elif plant["Pmax"] < 0:
                print("Pmax >= 0 must be satisfied for plant #%d" % (i + 1))
                self.ct.pop("new_plant")
                return
            if "Pmin" not in plant.keys():
                plant["Pmin"] = 0
            elif plant["Pmin"] < 0 or plant["Pmin"] > plant["Pmax"]:
                print("0 <= Pmin <= Pmax must be satisfied for plant #%d" % (i + 1))
                self.ct.pop("new_plant")
                return
            if plant["type"] in _renewable_resource:
                lon = self.grid.bus.loc[plant["bus_id"]].lon
                lat = self.grid.bus.loc[plant["bus_id"]].lat
                plant_same_type = self.grid.plant.groupby("type").get_group(
                    plant["type"]
                )
                neighbor_id = find_closest_neighbor(
                    (lon, lat), plant_same_type[["lon", "lat"]].values
                )
                plant["plant_id_neighbor"] = plant_same_type.iloc[neighbor_id].name
            else:
                for c in ["0", "1", "2"]:
                    if "c" + c not in plant.keys():
                        print("Missing key c%s for plant #%d" % (c, i + 1))
                        self.ct.pop("new_plant")
                        return
                    elif plant["c" + c] < 0:
                        print("c%s >= 0 must be satisfied for plant #%d" % (c, i + 1))
                        self.ct.pop("new_plant")
                        return

            self.ct["new_plant"].append(plant)

    def write(self, scenario_id):
        """Saves change table to disk.

        :param str scenario_id: scenario index.
        :raises IOError: if file already exists on local machine.
        """
        if not os.path.exists(server_setup.LOCAL_DIR):
            os.makedirs(server_setup.LOCAL_DIR)

        file_name = os.path.join(server_setup.LOCAL_DIR, scenario_id + "_ct.pkl")
        if os.path.isfile(file_name) is False:
            print("Writing %s" % file_name)
            pickle.dump(self.ct, open(file_name, "wb"))
        else:
            raise IOError("%s already exists" % file_name)
