import copy

import numpy as np
import pandas as pd

from powersimdata.utility.distance import haversine


class TransformGrid:
    """Transforms grid according to operations listed in change table."""

    def __init__(self, grid, ct):
        """Constructor

        :param powersimdata.input.grid.Grid grid: a Grid object.
        :param dict ct: change table.
        """
        self.grid = copy.deepcopy(grid)
        self.ct = copy.deepcopy(ct)
        self.gen_types = [
            "biomass",
            "coal",
            "dfo",
            "geothermal",
            "ng",
            "nuclear",
            "hydro",
            "solar",
            "wind",
            "wind_offshore",
            "other",
        ]
        self.thermal_gen_types = ["coal", "dfo", "geothermal", "ng", "nuclear"]

    def get_grid(self):
        """Returns the transformed grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        if bool(self.ct):
            self._apply_change_table()
        return self.grid

    def _apply_change_table(self):
        """Apply changes listed in change table to the grid."""
        # First scale by zones, so that zone factors are not applied to additions.
        for g in self.gen_types:
            if g in self.ct.keys():
                self._scale_gen_by_zone(g)
            if f"{g}_cost" in self.ct.keys():
                self._scale_gencost_by_zone(g)
            if f"{g}_pmin" in self.ct.keys():
                self._scale_gen_pmin_by_zone(g)

        if "branch" in self.ct.keys():
            self._scale_branch_by_zone()

        # Then, add new elements
        if "new_bus" in self.ct.keys():
            self._add_bus()

        if "new_branch" in self.ct.keys():
            self._add_branch()

        if "new_dcline" in self.ct.keys():
            self._add_dcline()

        if "new_plant" in self.ct.keys():
            self._add_gen()

        if "storage" in self.ct.keys():
            self._add_storage()

        # Scale by IDs, so that additions can be scaled.
        for g in self.gen_types:
            if g in self.ct.keys():
                self._scale_gen_by_id(g)
            if f"{g}_cost" in self.ct.keys():
                self._scale_gencost_by_id(g)
            if f"{g}_pmin" in self.ct.keys():
                self._scale_gen_pmin_by_id(g)

        if "branch" in self.ct.keys():
            self._scale_branch_by_id()

        if "dcline" in self.ct.keys():
            self._scale_dcline()

        # Finally, remove elements (so that removal doesn't cause downstream errors)
        if "remove_branch" in self.ct.keys():
            self._remove_branch()
        if "remove_bus" in self.ct.keys():
            self._remove_bus()

    def _scale_gen_by_zone(self, gen_type):
        """Scales capacity of generators, by zone. Also scales the associated generation
            cost curve (to maintain the same slopes at the start/end of the curve).

        :param str gen_type: type of generator.
        """
        if "zone_id" in self.ct[gen_type].keys():
            for zone_id, factor in self.ct[gen_type]["zone_id"].items():
                plant_id = (
                    self.grid.plant.groupby(["zone_id", "type"])
                    .get_group((zone_id, gen_type))
                    .index.tolist()
                )
                self._scale_gen_capacity(plant_id, factor)
                if gen_type in self.thermal_gen_types:
                    self._scale_gencost_by_capacity(plant_id, factor)

    def _scale_gen_by_id(self, gen_type):
        """Scales capacity of generators by ID. Also scales the associated generation
            cost curve (to maintain the same slopes at the start/end of the curve).

        :param str gen_type: type of generator.
        """
        if "plant_id" in self.ct[gen_type].keys():
            for plant_id, factor in self.ct[gen_type]["plant_id"].items():
                self._scale_gen_capacity(plant_id, factor)
                if gen_type in self.thermal_gen_types:
                    self._scale_gencost_by_capacity(plant_id, factor)

    def _scale_gencost_by_zone(self, gen_type):
        """Scales cost of generators, by zone.

        :param str gen_type: type of generator.
        """
        cost_key = f"{gen_type}_cost"
        if "zone_id" in self.ct[cost_key].keys():
            for zone_id, factor in self.ct[cost_key]["zone_id"].items():
                plant_id = (
                    self.grid.plant.groupby(["zone_id", "type"])
                    .get_group((zone_id, gen_type))
                    .index.tolist()
                )
                self.grid.gencost["before"].loc[plant_id, ["c0", "c1", "c2"]] *= factor

    def _scale_gencost_by_id(self, gen_type):
        """Scales cost of generators, by ID.

        :param str gen_type: type of generator.
        """
        cost_key = f"{gen_type}_cost"
        if "plant_id" in self.ct[cost_key].keys():
            for plant_id, factor in self.ct[cost_key]["plant_id"].items():
                self.grid.gencost["before"].loc[plant_id, ["c0", "c1", "c2"]] *= factor

    def _scale_gen_pmin_by_zone(self, gen_type):
        """Scales minimum generation of generators, by zone.

        :param str gen_type: type of generator.
        """
        pmin_key = f"{gen_type}_pmin"
        if "zone_id" in self.ct[pmin_key].keys():
            for zone_id, factor in self.ct[pmin_key]["zone_id"].items():
                plant_id = (
                    self.grid.plant.groupby(["zone_id", "type"])
                    .get_group((zone_id, gen_type))
                    .index.tolist()
                )
                self.grid.plant.loc[plant_id, "Pmin"] *= factor

    def _scale_gen_pmin_by_id(self, gen_type):
        """Scales minimum generation of generators, by ID.

        :param str gen_type: type of generator.
        """
        pmin_key = f"{gen_type}_pmin"
        if "plant_id" in self.ct[pmin_key].keys():
            for plant_id, factor in self.ct[pmin_key]["plant_id"].items():
                self.grid.plant.loc[plant_id, "Pmin"] *= factor

    def _scale_gen_capacity(self, plant_id, factor):
        """Scales capacity of plants.

        :param int/list plant_id: plant identification number(s).
        :param float factor: scaling factor.
        """
        self.grid.plant.loc[plant_id, "Pmax"] *= factor
        self.grid.plant.loc[plant_id, "Pmin"] *= factor

    def _scale_gencost_by_capacity(self, plant_id, factor):
        """Scales generation cost curves along with capacity, such that the start/end
            slopes are consistent before and after.

        :param int/list plant_id: plant identification number(s).
        :param float factor: scaling factor.
        :return:
        """
        self.grid.gencost["before"].loc[plant_id, "c0"] *= factor
        if factor != 0:
            self.grid.gencost["before"].loc[plant_id, "c2"] /= factor

    def _scale_branch_by_zone(self):
        """Scales capacity of AC lines, by zone, for lines entirely within that zone."""
        if "zone_id" in self.ct["branch"].keys():
            for zone_id, factor in self.ct["branch"]["zone_id"].items():
                branch_id = (
                    self.grid.branch.groupby(["from_zone_id", "to_zone_id"])
                    .get_group((zone_id, zone_id))
                    .index.tolist()
                )
                self._scale_branch_capacity(branch_id, factor)

    def _scale_branch_by_id(self):
        """Scales capacity of AC lines, by ID."""
        if "branch_id" in self.ct["branch"].keys():
            for branch_id, factor in self.ct["branch"]["branch_id"].items():
                self._scale_branch_capacity(branch_id, factor)

    def _scale_branch_capacity(self, branch_id, factor):
        """Scales capacity of AC lines.

        :param int/list branch_id: branch identification number(s)
        :param float factor: scaling factor
        """
        self.grid.branch.loc[branch_id, "rateA"] *= factor
        self.grid.branch.loc[branch_id, "x"] /= factor

    def _scale_dcline(self):
        """Scales capacity of HVDC lines."""
        for dcline_id, factor in self.ct["dcline"]["dcline_id"].items():
            self.grid.dcline.loc[dcline_id, "Pmin"] *= factor
            self.grid.dcline.loc[dcline_id, "Pmax"] *= factor
            if factor == 0:
                self.grid.dcline.loc[dcline_id, "status"] = 0

    def _add_branch(self):
        """Adds branch(es) to the grid."""
        v2x = voltage_to_x_per_distance(self.grid)
        for entry in self.ct["new_branch"]:
            new_branch = {c: 0 for c in self.grid.branch.columns}
            from_bus_id = entry["from_bus_id"]
            to_bus_id = entry["to_bus_id"]
            interconnect = self.grid.bus.loc[from_bus_id].interconnect
            from_zone_id = self.grid.bus.loc[from_bus_id].zone_id
            to_zone_id = self.grid.bus.loc[to_bus_id].zone_id
            from_zone_name = self.grid.id2zone[from_zone_id]
            to_zone_name = self.grid.id2zone[to_zone_id]
            from_lon = self.grid.bus.loc[from_bus_id].lon
            from_lat = self.grid.bus.loc[from_bus_id].lat
            to_lon = self.grid.bus.loc[to_bus_id].lon
            to_lat = self.grid.bus.loc[to_bus_id].lat
            from_basekv = v2x[self.grid.bus.loc[from_bus_id].baseKV]
            to_basekv = v2x[self.grid.bus.loc[to_bus_id].baseKV]
            distance = haversine((from_lat, from_lon), (to_lat, to_lon))
            x = distance * np.mean([from_basekv, to_basekv])

            new_branch["from_bus_id"] = entry["from_bus_id"]
            new_branch["to_bus_id"] = entry["to_bus_id"]
            new_branch["status"] = 1
            new_branch["ratio"] = 0
            new_branch["branch_device_type"] = "Line"
            new_branch["rateA"] = entry["Pmax"]
            new_branch["interconnect"] = interconnect
            new_branch["from_zone_id"] = from_zone_id
            new_branch["to_zone_id"] = to_zone_id
            new_branch["from_zone_name"] = from_zone_name
            new_branch["to_zone_name"] = to_zone_name
            new_branch["from_lon"] = from_lon
            new_branch["from_lat"] = from_lat
            new_branch["to_lon"] = to_lon
            new_branch["to_lat"] = to_lat
            new_branch["x"] = x
            new_index = [self.grid.branch.index[-1] + 1]
            self.grid.branch = self.grid.branch.append(
                pd.DataFrame(new_branch, index=new_index), sort=False
            )

    def _add_bus(self):
        bus = self.grid.bus
        zone2interconnect = {
            k: v[0] for k, v in bus.groupby("zone_id").interconnect.unique().items()
        }
        latlon2sub = self.grid.sub.groupby(["lat", "lon"]).groups
        for entry in self.ct["new_bus"]:
            # Add to the bus dataframe
            new_bus = {c: 0 for c in bus.columns}
            new_bus["type"] = 1
            new_bus["Pd"] = entry["Pd"]
            new_bus["zone_id"] = entry["zone_id"]
            new_bus["Vm"] = 1
            new_bus["baseKV"] = entry["baseKV"]
            new_bus["loss_zone"] = 1
            new_bus["Vmax"] = 1.1
            new_bus["Vmin"] = 0.9
            interconnect = zone2interconnect[entry["zone_id"]]
            new_bus["interconnect"] = interconnect
            lat, lon = entry["lat"], entry["lon"]
            new_bus["lat"] = lat
            new_bus["lon"] = lon
            new_bus_index = [self.grid.bus.index.max() + 1]
            self.grid.bus = self.grid.bus.append(
                pd.DataFrame(new_bus, index=new_bus_index), sort=False
            )
            # Add to substation & bus2sub mapping dataframes
            if (lat, lon) in latlon2sub:
                # If there are multiple matching substations, arbitrarily grab the first
                sub_id = latlon2sub[(lat, lon)][0]
                new_row = pd.DataFrame(
                    {"sub_id": sub_id, "interconnect": interconnect},
                    index=new_bus_index,
                )
                self.grid.bus2sub = self.grid.bus2sub.append(new_row, sort=False)
            else:
                # Create a new substation
                sub = self.grid.sub
                new_sub_id = sub.index.max() + 1
                interconnect_sub = sub[sub.interconnect == interconnect]
                new_interconnect_sub_id = interconnect_sub.interconnect_sub_id.max() + 1
                new_row = pd.DataFrame(
                    {"sub_id": new_sub_id, "interconnect": interconnect},
                    index=new_bus_index,
                )
                self.grid.bus2sub = self.grid.bus2sub.append(new_row, sort=False)
                new_row = pd.DataFrame(
                    {
                        "name": f"NEW {new_sub_id}",
                        "interconnect_sub_id": new_interconnect_sub_id,
                        "lat": lat,
                        "lon": lon,
                        "interconnect": interconnect,
                    },
                    index=[new_sub_id],
                )
                self.grid.sub = sub.append(new_row, sort=False)
                latlon2sub[(lat, lon)] = [new_sub_id]

    def _add_dcline(self):
        """Adds HVDC line(s) to the grid"""
        for entry in self.ct["new_dcline"]:
            new_dcline = {c: 0 for c in self.grid.dcline.columns}
            from_bus_id = entry["from_bus_id"]
            to_bus_id = entry["to_bus_id"]
            from_interconnect = self.grid.bus.loc[from_bus_id].interconnect
            to_interconnect = self.grid.bus.loc[to_bus_id].interconnect
            new_dcline["from_bus_id"] = entry["from_bus_id"]
            new_dcline["to_bus_id"] = entry["to_bus_id"]
            new_dcline["status"] = 1
            new_dcline["Pf"] = entry["Pmax"]
            new_dcline["Pt"] = 0.98 * entry["Pmax"]
            new_dcline["Pmin"] = entry["Pmin"]
            new_dcline["Pmax"] = entry["Pmax"]
            new_dcline["from_interconnect"] = from_interconnect
            new_dcline["to_interconnect"] = to_interconnect
            new_index = [self.grid.dcline.index[-1] + 1]
            self.grid.dcline = self.grid.dcline.append(
                pd.DataFrame(new_dcline, index=new_index), sort=False
            )

    def _add_gen(self):
        """Adds generator(s) to the grid."""
        self._add_plant()
        self._add_gencost()

    def _add_plant(self):
        """Adds plant to the grid"""
        for entry in self.ct["new_plant"]:
            new_plant = {c: 0 for c in self.grid.plant.columns}
            bus_id = entry["bus_id"]
            interconnect = self.grid.bus.loc[bus_id].interconnect
            zone_id = self.grid.bus.loc[bus_id].zone_id
            zone_name = self.grid.id2zone[zone_id]
            lon = self.grid.bus.loc[bus_id].lon
            lat = self.grid.bus.loc[bus_id].lat

            new_plant["bus_id"] = bus_id
            new_plant["type"] = entry["type"]
            new_plant["Pmin"] = entry["Pmin"]
            new_plant["Pmax"] = entry["Pmax"]
            new_plant["status"] = 1
            new_plant["interconnect"] = interconnect
            new_plant["zone_id"] = zone_id
            new_plant["zone_name"] = zone_name
            new_plant["lon"] = lon
            new_plant["lat"] = lat
            new_index = [self.grid.plant.index[-1] + 1]
            self.grid.plant = self.grid.plant.append(
                pd.DataFrame(new_plant, index=new_index), sort=False
            )

    def _add_gencost(self):
        """Adds generation cost curves."""
        for entry in self.ct["new_plant"]:
            new_gencost = {c: 0 for c in self.grid.gencost["before"].columns}
            bus_id = entry["bus_id"]
            new_gencost["type"] = 2
            new_gencost["n"] = 3
            new_gencost["interconnect"] = self.grid.bus.loc[bus_id].interconnect
            if entry["type"] in self.thermal_gen_types:
                new_gencost["c0"] = entry["c0"]
                new_gencost["c1"] = entry["c1"]
                new_gencost["c2"] = entry["c2"]
            new_index = [self.grid.gencost["before"].index[-1] + 1]
            self.grid.gencost["before"] = self.grid.gencost["before"].append(
                pd.DataFrame(new_gencost, index=new_index), sort=False
            )
            self.grid.gencost["after"] = self.grid.gencost["before"]

    def _add_storage(self):
        """Adds storage to the grid."""
        first_storage_id = self.grid.plant.index.max() + 1
        for i, entry in enumerate(self.ct["storage"]):
            storage_id = first_storage_id + i
            self._add_storage_unit(entry)
            self._add_storage_gencost()
            self._add_storage_genfuel()
            self._add_storage_data(storage_id, entry)

    def _add_storage_unit(self, entry):
        """Add storage unit.

        :param int bus_id: bus identification number.
        :param dict entry: storage details, containing at least "bus_id" and "capacity".
        """
        storage = self.grid.storage
        gen = {g: 0 for g in storage["gen"].columns}
        gen["bus_id"] = entry["bus_id"]
        gen["Vg"] = 1
        gen["mBase"] = 100
        gen["status"] = 1
        gen["Pmax"] = entry["capacity"]
        gen["Pmin"] = -1 * entry["capacity"]
        gen["ramp_10"] = entry["capacity"]
        gen["ramp_30"] = entry["capacity"]
        storage["gen"] = storage["gen"].append(gen, ignore_index=True, sort=False)
        # Maintain int columns after the append converts them to float
        storage["gen"] = storage["gen"].astype({"bus_id": "int", "status": "int"})

    def _add_storage_gencost(self):
        """Sets generation cost of storage unit."""
        gencost = {g: 0 for g in self.grid.storage["gencost"].columns}
        gencost["type"] = 2
        gencost["n"] = 3
        self.grid.storage["gencost"] = self.grid.storage["gencost"].append(
            gencost, ignore_index=True, sort=False
        )

    def _add_storage_genfuel(self):
        """Sets fuel type of storage unit."""
        self.grid.storage["genfuel"].append("ess")

    def _add_storage_data(self, storage_id, entry):
        """Sets storage data.

        :param int storage_id: storage identification number.
        :param dict entry: storage details, containing at least:
            "bus_id", "capacity".
        """
        storage = self.grid.storage
        data = {g: 0 for g in storage["StorageData"].columns}

        capacity = entry["capacity"]
        duration = entry["duration"]
        min_stor = entry["min_stor"]
        max_stor = entry["max_stor"]
        energy_value = entry["energy_value"]
        terminal_min = entry["terminal_min"]
        terminal_max = entry["terminal_max"]

        data["UnitIdx"] = storage_id
        data["ExpectedTerminalStorageMax"] = capacity * duration * terminal_max
        data["ExpectedTerminalStorageMin"] = capacity * duration * terminal_min
        data["InitialStorage"] = capacity * duration / 2  # Start with half
        data["InitialStorageLowerBound"] = capacity * duration / 2  # Start with half
        data["InitialStorageUpperBound"] = capacity * duration / 2  # Start with half
        data["InitialStorageCost"] = energy_value
        data["TerminalStoragePrice"] = energy_value
        data["MinStorageLevel"] = capacity * duration * min_stor
        data["MaxStorageLevel"] = capacity * duration * max_stor
        data["OutEff"] = entry["OutEff"]
        data["InEff"] = entry["InEff"]
        data["LossFactor"] = entry["LossFactor"]
        data["rho"] = 1
        storage["StorageData"] = storage["StorageData"].append(
            data, ignore_index=True, sort=False
        )
        # Maintain int columns after the append converts them to float
        storage["StorageData"] = storage["StorageData"].astype({"UnitIdx": "int"})

    def _remove_branch(self):
        """Removes branches."""
        branch = self.grid.branch
        self.grid.branch = branch.loc[~branch.index.isin(self.ct["remove_branch"])]

    def _remove_bus(self):
        """Removes buses."""
        bus = self.grid.bus
        self.grid.bus = bus.loc[~bus.index.isin(self.ct["remove_bus"])]

    def _remove_dcline(self):
        """Removes DC lines."""
        dcline = self.grid.dcline
        self.grid.dcline = dcline.loc[~dcline.index.isin(self.ct["remove_dcline"])]

    def _remove_plant(self):
        """Removes plants."""
        plant = self.grid.plant
        self.grid.plant = plant.loc[~plant.index.isin(self.ct["remove_plant"])]


def voltage_to_x_per_distance(grid):
    """Calculates reactance per distance for voltage level.

    :param powersimdata.input.grid.Grid grid: a Grid object instance.
    :return: (*dict*) -- bus voltage to average reactance per mile.
    """
    branch = grid.branch[grid.branch.branch_device_type == "Line"]
    distance = (
        branch[["from_lat", "from_lon", "to_lat", "to_lon"]]
        .apply(lambda x: haversine((x[0], x[1]), (x[2], x[3])), axis=1)
        .values
    )

    no_zero = np.nonzero(distance)[0]
    x_per_distance = (branch.iloc[no_zero].x / distance[no_zero]).values

    basekv = np.array([grid.bus.baseKV[i] for i in branch.iloc[no_zero].from_bus_id])

    v2x = {v: np.mean(x_per_distance[np.where(basekv == v)[0]]) for v in set(basekv)}

    return v2x
