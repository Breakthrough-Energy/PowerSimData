import copy

from powersimdata.input.input_data import InputData
from powersimdata.input.grid import Grid


class TransformProfile(object):
    """Transforms profile according to operations listed in change table.

    """

    def __init__(self, ssh_client, scenario_info, grid, ct):
        """Constructor

        :param paramiko.client.SSHClient ssh_client: session with an SSH server.
        :param dict scenario_info: scenario information.
        :param powersimdata.input.grid.Grid grid: a Grid object.
        :param dict ct: change table.
        """
        self._input_data = InputData(ssh_client)
        self.scenario_info = scenario_info
        self.grid = copy.deepcopy(grid)
        self.ct = copy.deepcopy(ct)
        self.scale_keys = {
            "wind": {"wind", "wind_offshore"},
            "solar": {"solar"},
            "hydro": {"hydro"},
            "demand": {"demand"},
        }
        self.n_new_plant = (
            0 if "new_plant" not in self.ct.keys() else len(self.ct["new_plant"])
        )
        self.base_plant = Grid(self.grid.interconnect).plant

    def _get_renewable_profile(self, resource):
        """Returns the transformed grid.

        :param str resource: *'hydro'*, *'solar'* or *'wind'*.
        :return: (*pandas.DataFrame*) -- power output for generators of
            specified type with plant identification number  as columns and
            UTC timestamp as index.
        """
        power_output = self._input_data.get_data(self.scenario_info, resource)
        if not bool(self.ct):
            return power_output
        else:
            if self.n_new_plant > 0:
                power_output = self._add_plant_profile(power_output, resource)
            if resource in self.ct.keys():
                power_output = self._scale_plant_profile(power_output, resource)
            return power_output

    def _add_plant_profile(self, profile, resource):
        """Add power output profile for plants added via the change table.

        :param pandas.DataFrame profile: power output profile with plant
            identification number as columns and UTC timestamp as index.
        :param resource: fuel type.
        :return: (*pandas.DataFrame*) -- power output profile with additional
            columns corresponding to new generators inserted to the grid via
            the change table.
        """
        new_plant_ids, neighbor_ids, scaling = [], [], []
        transformed_plant = self.grid.plant
        for i, entry in enumerate(self.ct["new_plant"]):
            if entry["type"] in self.scale_keys[resource]:
                new_plant_id = transformed_plant.index[-self.n_new_plant + i]
                new_plant_ids.append(new_plant_id)
                neighbor_id = entry["plant_id_neighbor"]
                neighbor_ids.append(neighbor_id)
                scaling.append(entry["Pmax"] / self.base_plant.loc[neighbor_id, "Pmax"])

        if len(new_plant_ids) > 0:
            neighbor_profiles = profile[neighbor_ids]
            new_profiles = neighbor_profiles.multiply(scaling, axis=1)
            new_profiles.columns = new_plant_ids
            joined_profiles = profile.join(new_profiles)
            return joined_profiles
        else:
            return profile

    def _scale_plant_profile(self, profile, resource):
        """Scales power output according to change table.

        :param pandas.DataFrame profile: power output profile with plant
            identification number as columns and UTC timestamp as index.
        :param resource: fuel type.
        :return: (*pandas.DataFrame*) -- scaled power output profile.
        """
        for r in self.scale_keys[resource]:
            if r in self.ct.keys() and "zone_id" in self.ct[r].keys():
                type_in_zone = self.base_plant.groupby(["zone_id", "type"])
                for z, f in self.ct[r]["zone_id"].items():
                    plant_id = type_in_zone.get_group((z, r)).index.tolist()
                    profile.loc[:, plant_id] *= f
            if r in self.ct.keys() and "plant_id" in self.ct[r].keys():
                for i, f in self.ct[r]["plant_id"].items():
                    profile.loc[:, i] *= f

        return profile

    def _get_demand_profile(self):
        """Returns scaled demand profile.

        :return: (*pandas.DataFrame*) -- data frame of demand.
        """
        demand = self._input_data.get_data(self.scenario_info, "demand")
        if bool(self.ct) and "demand" in list(self.ct.keys()):
            for key, value in self.ct["demand"]["zone_id"].items():
                print(
                    "Multiply demand in %s (#%d) by %.2f"
                    % (self.grid.id2zone[key], key, value)
                )
                demand.loc[:, key] *= value
        return demand

    def get_profile(self, name):
        """Returns profile.

        :param str name: either *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*pandas.DataFrame*) -- profile.
        :raises ValueError: if argument not one of *'demand'*, *'hydro'*, *'solar'* or
            *'wind'*.
        """
        possible = ["demand", "hydro", "solar", "wind"]
        if name not in possible:
            raise ValueError("Choose from %s" % " | ".join(possible))
        elif name == "demand":
            return self._get_demand_profile()
        else:
            return self._get_renewable_profile(name)
