import copy
import os
import pickle
from itertools import chain

from powersimdata.design.transmission.upgrade import (
    scale_congested_mesh_branches,
    scale_renewable_stubs,
)
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.utility import server_setup
from powersimdata.utility.distance import find_closest_neighbor

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


def ordinal(n):
    """Translate a 0-based index into a 1-based ordinal, e.g. 0 -> 1st, 1 -> 2nd, etc.

    :param int n: the index to be translated.
    :return: (*str*) -- Ordinal.
    """
    ord_dict = {1: "st", 2: "nd", 3: "rd"}
    return str(n + 1) + ord_dict.get((n + 1) if (n + 1) < 20 else (n + 1) % 10, "th")


class ChangeTable:
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
        value is a list. Each entry in this list is a dictionary enclosing all the
        information needed to add a new storage device to the grid. The keys in the
        dictionary are: *'bus_id'*, *'capacity'*, "duration", "min_stor", "max_stor",
        "energy_value", "InEff", "OutEff", "LossFactor", "terminal_min",
        and "terminal_max". See the :meth:`add_storage_capacity` method for details.
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
    * *'new_bus'*:
        value is a list. Each entry in this list is a dictionary enclosing
        all the information needed to add a new bus to the grid. The
        keys in the dictionary are: *'lat'*, *'lon'*, one of *'zone_id'*/*'zone_name'*,
        and optionally *'Pd'*, specifying the location of the bus, the demand zone, and
        optionally the nominal demand at that bus (defaults to 0).
    * *'remove_branch'*:
        value is a set. Each entry in this set is a branch ID to be removed.
    * *'remove_bus'*:
        value is a set. Each entry in this set is a bus ID to be removed.
    * *'remove_dcline'*:
        value is a set. Each entry in this set is a DC line ID to be removed.
    * *'remove_plant'*:
        value is a set. Each entry in this set is a plant ID to be removed.
    """

    def __init__(self, grid):
        """Constructor.

        :param powersimdata.input.grid.Grid grid: a Grid object
        """
        self.grid = grid
        self.ct = {}
        self._new_element_caches = {
            k: {} for k in {"branch", "bus", "dcline", "plant", "storage_gen"}
        }

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
            If None (default), everything is cleared.
        """
        # Clear all
        if which is None:
            self.ct.clear()
            return
        # Input validation
        allowed = {"branch", "bus", "dcline", "demand", "plant", "storage"}
        if isinstance(which, str):
            which = {which}
        if not isinstance(which, set):
            raise TypeError("Which must be a str, a set, or None (defaults to all)")
        if not which <= allowed:
            raise ValueError("which must contain only: " + " | ".join(allowed))
        # Clear only top-level keys specified in which
        for key in {"demand", "storage"}:
            if key in which:
                del self.ct[key]
        # Clear multiple keys for each entry in which
        for line_type in {"branch", "dcline"}:
            if line_type in which:
                for prefix in {"", "new_", "remove_"}:
                    key = prefix + line_type
                    if key in self.ct:
                        del self.ct[key]
        if "bus" in which:
            for prefix in {"new_", "remove_"}:
                key = prefix + "bus"
                if key in self.ct:
                    del self.ct[key]
        if "plant" in which:
            for key in {"new_plant", "remove_plant"}:
                if key in self.ct:
                    del self.ct[key]
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
                anticipated_plant = self._get_transformed_df("plant")
                diff = set(plant_id.keys()) - set(anticipated_plant.index)
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
        anticipated_branch = self._get_transformed_df("branch")
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
                diff = set(branch_id.keys()) - set(anticipated_branch.index)
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
        anticipated_dcline = self._get_transformed_df("dcline")
        diff = set(dcline_id.keys()) - set(anticipated_dcline.index)
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

    def add_storage_capacity(self, info):
        """Sets storage parameters in change table.

        :param list info: each entry is a dictionary. The dictionary gathers
            the information needed to create a new storage device.
            Required keys: "bus_id", "capacity".
            "capacity" denotes the symmetric input and output power limits (MW).
            Optional keys: "duration", "min_stor", "max_stor", "energy_value", "InEff",
                "OutEff", "LossFactor", "terminal_min", "terminal_max".
            "duration" denotes the energy to power ratio (hours).
            "min_stor" denotes the minimum energy limit (unitless), e.g. 0.05 = 5%.
            "max_stor" denotes the maximum energy limit (unitless), e.g. 0.95 = 95%.
            "energy_value" denotes the value of stored energy at interval end ($/MWh).
            "InEff" denotes the input efficiency (unitless), e.g. 0.95 = 95%.
            "OutEff" denotes the output efficiency (unitless), e.g. 0.95 = 95%.
            "LossFactor" denotes the per-hour relative losses,
            e.g. 0.01 means that 1% of the current state of charge is lost per hour).
            "terminal_min" denotes the minimum state of charge at interval end,
            e.g. 0.5 means that the storage must end the interval with at least 50%.
            "terminal_max" denotes the maximum state of charge at interval end,
            e.g. 0.9 means that the storage must end the interval with no more than 90%.
        :raises TypeError: if ``info`` is not a list.
        :raises ValueError: if any of the new storages to be added have bad values.
        """
        if not isinstance(info, list):
            raise TypeError("Argument enclosing new storage(s) must be a list")

        info = copy.deepcopy(info)
        new_storages = []
        required = {"bus_id", "capacity"}
        optional = {
            "duration",
            "min_stor",
            "max_stor",
            "energy_value",
            "InEff",
            "OutEff",
            "LossFactor",
            "terminal_min",
            "terminal_max",
        }
        anticipated_bus = self._get_transformed_df("bus")
        for i, storage in enumerate(info):
            self._check_entry_keys(storage, i, "storage", required, None, optional)
            if storage["bus_id"] not in anticipated_bus.index:
                raise ValueError(
                    f"No bus id {storage['bus_id']} available for {ordinal(i)} storage"
                )
            for o in optional:
                if o not in storage:
                    storage[o] = self.grid.storage[o]
            for k, v in storage.items():
                if not isinstance(v, (int, float)):
                    err_msg = f"values must be numeric, bad type for {ordinal(i)} {k}"
                    raise ValueError(err_msg)
                if v < 0:
                    raise ValueError(
                        f"values must be non-negative, bad value for {ordinal(i)} {k}"
                    )
            for k in {"min_stor", "max_stor", "InEff", "OutEff", "LossFactor"}:
                if storage[k] > 1:
                    raise ValueError(
                        f"value for {k} must be <=1, bad value for {ordinal(i)} storage"
                    )
            new_storages.append(storage)
        if "storage" not in self.ct:
            self.ct["storage"] = []
        self.ct["storage"] += new_storages

    def add_dcline(self, info):
        """Adds HVDC line(s).

        :param list info: each entry is a dictionary. The dictionary gathers
            the information needed to create a new dcline.
            Required keys: "from_bus_id", "to_bus_id".
            Optional keys: "capacity", "Pmax", "Pmin".
            "capacity" denotes a bidirectional power limit (MW).
            "Pmax" denotes a limit on power flowing from 'from' end to 'to' end.
            "Pmin" denotes a limit on power flowing from 'from' end to 'to' end.
            Either "capacity" XOR ("Pmax" and "Pmin") must be provided.
            `capacity: 200` is equivalent to `Pmax: 200, Pmin: -200`.
        :raises TypeError: if ``info`` is not a list.
        """
        if not isinstance(info, list):
            raise TypeError("Argument enclosing new HVDC line(s) must be a list")
        self._add_line("new_dcline", info)

    def add_branch(self, info):
        """Sets parameters of new branch(es) in change table.

        :param list info: each entry is a dictionary. The dictionary gathers
            the information needed to create a new branch.
            Required keys: "from_bus_id", "to_bus_id", "capacity".
        :raises TypeError: if ``info`` is not a list.
        """
        if not isinstance(info, list):
            raise TypeError("Argument enclosing new AC line(s) must be a list")
        self._add_line("new_branch", info)

    def _check_entry_keys(self, entry, n, key, required, xor_sets=None, optional=None):
        """Check the validity of the dict keys used to add new components to the
        network (e.g. plants, AC lines), checking for: missing keys, extra keys, or
        incompatible sets of keys.

        :param dict entry: dict of key/value pairs for a new entry.
        :param int n: index of the new entry (used in error messages).
        :param str key: type of new entry (used in error messages).
        :param set required: keys which must be specified.
        :param set xor_sets: set of tuples, for which exactly one key must be specified.
        :param set optional: set of acceptable keys which are not required or in an xor
            set.
        :raises TypeError: if entry is not a dict.
        :raises ValueError: if any required keys are missing, the number of specified
            keys in each xor set is not exactly one, or an unexpected key is received.
        """
        xor_sets = set(tuple()) if xor_sets is None else xor_sets
        optional = set() if optional is None else optional
        nth = ordinal(n)
        if not isinstance(entry, dict):
            raise TypeError(f"Each entry must be a dictionary, error on {nth} {key}")
        if len(required - entry.keys()) > 0:
            missing_keys = required - entry.keys()
            raise ValueError(
                f"Each entry of {key} requires keys of: {', '.join(sorted(required))}. "
                f"Missing {sorted(missing_keys)} on {nth} entry, possibly others."
            )
        allowable_keys = required | optional | set().union(*xor_sets)
        if not set(entry.keys()) <= allowable_keys:
            unknown_keys = set(entry.keys()) - allowable_keys
            err_msg = f"Got unknown keys in {nth} {key}: {', '.join(unknown_keys)}"
            raise ValueError(err_msg)
        for xor_set in sorted(xor_sets):
            if len(xor_set & entry.keys()) != 1:
                err_msg = f"For {key}, must specify one of {xor_set} but not both"
                err_msg += f". Error on {nth} entry, possibly others"
                raise ValueError(err_msg)

    def _add_line(self, key, info):
        """Handles line(s) addition in change table.

        :param str key: key in change table. Either *'new_branch'* or *'new_dcline'*
        :param list info: parameters of the line.
        :raises ValueError: if any of the new lines to be added have nonsensical values.
        """
        info = copy.deepcopy(info)
        anticipated_bus = self._get_transformed_df("bus")
        new_lines = []
        required = {"from_bus_id", "to_bus_id"}
        xor_sets = {("capacity", "Pmax"), ("capacity", "Pmin")}
        optional = {"Pmin"}
        for i, line in enumerate(info):
            self._check_entry_keys(line, i, key, required, xor_sets, optional)
            start = line["from_bus_id"]
            end = line["to_bus_id"]
            if start not in anticipated_bus.index:
                raise ValueError(
                    "No bus with the following id for line #%d: %d" % (i + 1, start)
                )
            if end not in anticipated_bus.index:
                raise ValueError(
                    "No bus with the following id for line #%d: %d" % (i + 1, end)
                )
            if start == end:
                raise ValueError(f"to/from buses of line #{i + 1} must be different")
            if "capacity" in line:
                if not isinstance(line["capacity"], (int, float)):
                    raise ValueError("'capacity' must be a number (int/float)")
                if line["capacity"] < 0:
                    raise ValueError("capacity of line #%d must be positive" % (i + 1))
                # Everything looks good, let's translate this to Pmin/Pmax
                line["Pmax"] = line["capacity"]
                line["Pmin"] = -1 * line["capacity"]
                del line["capacity"]
            elif {"Pmin", "Pmax"} < set(line.keys()):
                if key == "new_branch":
                    err_msg = "Can't independently set Pmin & Pmax for AC branches"
                    raise ValueError(err_msg)
                for p in {"Pmin", "Pmax"}:
                    if not isinstance(line[p], (int, float)):
                        raise ValueError(f"'{p}' must be a number (int/float)")
                if line["Pmin"] > line["Pmax"]:
                    raise ValueError("Pmin cannot be greater than Pmax")
            else:
                raise ValueError("Must specify either 'capacity' or Pmin and Pmax")
            if (
                key == "new_branch"
                and anticipated_bus.interconnect[start]
                != anticipated_bus.interconnect[end]
            ):
                raise ValueError(
                    "Buses of line #%d must be in same interconnect" % (i + 1)
                )
            elif (
                anticipated_bus.lat[start] == anticipated_bus.lat[end]
                and anticipated_bus.lon[start] == anticipated_bus.lon[end]
            ):
                raise ValueError("Distance between buses of line #%d is 0" % (i + 1))
            new_lines.append(line)

        if key not in self.ct:
            self.ct[key] = []
        self.ct[key] += new_lines

    def add_plant(self, info):
        """Sets parameters of new generator(s) in change table.

        :param list info: each entry is a dictionary. The dictionary gathers
            the information needed to create a new generator.
            Required keys: "bus_id", "Pmax", "type".
            Optional keys: "c0", "c1", "c2", "Pmin".
            "c0", "c1", and "c2" are the coefficients for the cost curve, representing
            the fixed cost ($/hour), linear cost ($/MWh), and quadratic cost ($/MW^2·h).
            These are optional for hydro, solar, and wind, and required for other types.
        :raises TypeError: if ``info`` is not a list.
        :raises ValueError: if any of the new plants to be added have bad values.
        """
        if not isinstance(info, list):
            raise TypeError("Argument enclosing new plant(s) must be a list")

        info = copy.deepcopy(info)
        anticipated_bus = self._get_transformed_df("bus")
        new_plants = []
        required = {"bus_id", "Pmax", "type"}
        optional = {"c0", "c1", "c2", "Pmin"}
        for i, plant in enumerate(info):
            self._check_entry_keys(plant, i, "plant", required, None, optional)
            self._check_resource(plant["type"])
            if plant["bus_id"] not in anticipated_bus.index:
                raise ValueError(
                    f"No bus id {plant['bus_id']} available for plant #{i + 1}"
                )
            if plant["Pmax"] < 0:
                raise ValueError(f"Pmax >= 0 must be satisfied for plant #{i + 1}")
            if "Pmin" not in plant.keys():
                plant["Pmin"] = 0
            if plant["Pmin"] < 0 or plant["Pmin"] > plant["Pmax"]:
                err_msg = f"0 <= Pmin <= Pmax must be satisfied for plant #{i + 1}"
                raise ValueError(err_msg)
            if plant["type"] in _renewable_resource:
                lon = anticipated_bus.loc[plant["bus_id"]].lon
                lat = anticipated_bus.loc[plant["bus_id"]].lat
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
                        raise ValueError(f"Missing key c{c} for plant #{i + 1}")
                    elif plant["c" + c] < 0:
                        err_msg = f"c{c} >= 0 must be satisfied for plant #{i + 1}"
                        raise ValueError(err_msg)
            new_plants.append(plant)

        if "new_plant" not in self.ct:
            self.ct["new_plant"] = []
        self.ct["new_plant"] += new_plants

    def add_bus(self, info):
        """Sets parameters of new bus(es) in change table.

        :param list info: each entry is a dictionary. The dictionary gathers
            the information needed to create a new bus.
            Required keys: "lat", "lon", ["zone_id" XOR "zone_name"].
            Optional key: "Pd", "baseKV".
        :raises TypeError: if ``info`` is not a list.
        :raises ValueError: if any new bus doesn't have appropriate keys/values.
        """
        if not isinstance(info, list):
            raise TypeError("Argument enclosing new bus(es) must be a list")

        info = copy.deepcopy(info)
        new_buses = []
        required = {"lat", "lon"}
        xor_sets = {("zone_id", "zone_name")}
        defaults = {"Pd": 0, "baseKV": 230}
        for i, new_bus in enumerate(info):
            self._check_entry_keys(
                new_bus, i, "new_bus", required, xor_sets, defaults.keys()
            )
            for l in {"lat", "lon"}:
                if not isinstance(new_bus[l], (int, float)):
                    raise ValueError(f"{l} must be numeric (int/float)")
            if abs(new_bus["lat"]) > 90:
                raise ValueError("'lat' must be between -90 and +90")
            if abs(new_bus["lon"]) > 180:
                raise ValueError("'lon' must be between -180 and +180")
            if "zone_id" in new_bus and new_bus["zone_id"] not in self.grid.id2zone:
                zone_id = new_bus["zone_id"]
                raise ValueError(f"zone_id {zone_id} not present in Grid")
            if "zone_name" in new_bus:
                try:
                    new_bus["zone_id"] = self.grid.zone2id[new_bus["zone_name"]]
                except KeyError:
                    zone_name = new_bus["zone_name"]
                    raise ValueError(f"zone_name {zone_name} not present in Grid")
                del new_bus["zone_name"]
            if "Pd" in new_bus:
                if not isinstance(new_bus["Pd"], (int, float)):
                    raise ValueError("Pd must be numeric (int/float)")
            else:
                new_bus["Pd"] = defaults["Pd"]
            if "baseKV" in new_bus:
                if not isinstance(new_bus["baseKV"], (int, float)):
                    raise ValueError("baseKV must be numeric (int/float)")
                if new_bus["baseKV"] <= 0:
                    raise ValueError("baseKV must be positive")
            else:
                new_bus["baseKV"] = defaults["baseKV"]
            new_buses.append(new_bus)
        if "new_bus" not in self.ct:
            self.ct["new_bus"] = []
        self.ct["new_bus"] += new_buses

    def _get_transformed_df(self, table):
        """Get a post-transformation data table, for use with adding elements at new
        buses, or scaling new elements. Transformed tables are cached to avoid
        unnecessary re-calculation of identical tables.

        :param str table: the table of the grid to be fetched:
            'branch', 'bus', 'dcline', 'plant', or 'storage_gen'.
        :return: (*pandas.DataFrame*) -- the post-transformation table.
        """
        if table == "storage_gen":
            # Storage is a special case, since it's a dict of data frames
            modification_keys = ["storage"]
            try:
                cache_key = tuple(tuple(sorted(b.items())) for b in self.ct["storage"])
            except KeyError:
                # No 'storage' key, so we can just return the original 'gen' table
                return self.grid.storage["gen"]
            if cache_key in self._new_element_caches[table]:
                return self._new_element_caches[table][cache_key]
            else:
                gen = TransformGrid(self.grid, self.ct).get_grid().storage["gen"]
                self._new_element_caches[table][cache_key] = gen
                return gen.copy()
        # For all other tables, look at change table keys for additions & deletions
        modification_keys = [f"new_{table}", f"remove_{table}"]
        cache_key = tuple(
            tuple(sorted(b.items())) for b in self.ct.get(f"new_{table}", {})
        )
        cache_key += (
            f"remove_{table}",
            tuple(sorted(self.ct.get(f"remove_{table}", {}))),
        )
        if table == "plant":
            # For the plant table, also look at scaling (potentially to zero)
            # These are needed to validate whether buses can be removed
            modification_keys += sorted(self.grid.plant["type"].unique())
            cache_key += tuple(
                chain.from_iterable(
                    [
                        tuple([subkey] + sorted(subdict.items()))
                        for k in modification_keys[1:]
                        for subkey, subdict in self.ct.get(k, {}).items()
                    ]
                )
            )
        if not any(m in self.ct for m in modification_keys):
            return getattr(self.grid, table)
        if cache_key in self._new_element_caches[table]:
            return self._new_element_caches[table][cache_key]
        else:
            transformed = getattr(TransformGrid(self.grid, self.ct).get_grid(), table)
            self._new_element_caches[table][cache_key] = transformed
            return transformed.copy()

    def remove_branch(self, info):
        """Remove one or more branches.

        :param int/iterable info: iterable of branch indices, or a single branch index.
        :raises ValueError: if ``info`` contains one or more entries not present in the
            branch table index.
        """
        if isinstance(info, int):
            info = {info}
        diff = set(info) - set(self._get_transformed_df("branch").index)
        if len(diff) != 0:
            raise ValueError(f"No branch with the following id(s): {sorted(diff)}")
        if "remove_branch" not in self.ct:
            self.ct["remove_branch"] = set()
        self.ct["remove_branch"] |= set(info)
        self._check_for_islanded_load_buses()

    def remove_bus(self, info):
        """Remove one or more buses.

        :param int/iterable info: iterable of bus indices, or a single bus index.
        :raises ValueError: if ``info`` contains one or more entries not present in the
            bus table index.
        """
        if isinstance(info, int):
            info = {info}
        # Check whether all buses to be removed are present in the grid
        diff = set(info) - set(self._get_transformed_df("bus").index)
        if len(diff) != 0:
            raise ValueError(f"No bus with the following id(s): {sorted(diff)}")
        # Check whether there exist any plants with non-zero capacity at these buses
        anticipated_plant = self._get_transformed_df("plant").query("Pmax > 0")
        plants_at_removal_buses = set(info) & set(anticipated_plant.bus_id)
        if len(plants_at_removal_buses) > 0:
            raise ValueError(
                f"Generators exist at bus id(s): {sorted(plants_at_removal_buses)}"
            )
        # Check whether storage exists at these buses
        anticipated_storage = self._get_transformed_df("storage_gen")
        storage_at_removal_buses = set(info) & set(anticipated_storage.bus_id)
        if len(storage_at_removal_buses) > 0:
            raise ValueError(
                f"Storage units exist at bus id(s): {sorted(storage_at_removal_buses)}"
            )
        # Check whether there exist branches or DC lines at these buses
        for table in ("branch", "dcline"):
            anticipated = self._get_transformed_df(table)
            overlap = anticipated.query("from_bus_id in @info or to_bus_id in @info")
            if len(overlap) > 0:
                raise ValueError(
                    f"These {table} IDs connect to a bus to be removed: {overlap.index}"
                )
        # All checks have passed, and we can add this to the change table
        if "remove_bus" not in self.ct:
            self.ct["remove_bus"] = set()
        self.ct["remove_bus"] |= set(info)

    def remove_dcline(self, info):
        """Remove one or more DC lines.

        :param int/iterable info: iterable of DC line indices, or a single index.
        :raises ValueError: if ``info`` contains one or more entries not present in the
            dcline table index.
        """
        if isinstance(info, int):
            info = {info}
        diff = set(info) - set(self._get_transformed_df("dcline").index)
        if len(diff) != 0:
            raise ValueError(f"No DC line with the following id(s): {sorted(diff)}")
        if "remove_dcline" not in self.ct:
            self.ct["remove_dcline"] = set()
        self.ct["remove_dcline"] |= set(info)

    def remove_plant(self, info):
        """Remove one or more plants.

        :param int/iterable info: iterable of plant indices, or a single plant index.
        :raises ValueError: if ``info`` contains one or more entries not present in the
            plant table index.
        """
        if isinstance(info, int):
            info = {info}
        diff = set(info) - set(self._get_transformed_df("plant").index)
        if len(diff) != 0:
            raise ValueError(f"No plant with the following id(s): {sorted(diff)}")
        if "remove_plant" not in self.ct:
            self.ct["remove_plant"] = set()
        self.ct["remove_plant"] |= set(info)

    def _check_for_islanded_load_buses(self):
        """Identifies buses with non-zero demand, with no connected lines, and warns."""
        bus = self._get_transformed_df("bus")
        connected_buses = set().union(
            *[
                set(self.grid.branch["from_bus_id"]),
                set(self.grid.branch["to_bus_id"]),
                set(self.grid.dcline["from_bus_id"]),
                set(self.grid.dcline["to_bus_id"]),
            ]
        )
        load_buses = set(bus.query("Pd > 0").index)
        diff = load_buses - connected_buses
        if len(diff) > 0:
            print(f"Warning: load buses connected to no lines exist: {sorted(diff)}")

    def write(self, scenario_id):
        """Saves change table to disk.

        :param str scenario_id: scenario index.
        :raises IOError: if file already exists on local machine.
        """
        file_name = os.path.join(server_setup.LOCAL_DIR, scenario_id + "_ct.pkl")
        if os.path.isfile(file_name) is False:
            print("Writing %s" % file_name)
            pickle.dump(self.ct, open(file_name, "wb"))
        else:
            raise IOError("%s already exists" % file_name)
