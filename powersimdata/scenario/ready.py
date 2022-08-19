import copy

from powersimdata.input.grid import Grid
from powersimdata.input.input_data import distribute_demand_from_zones_to_buses
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.scenario.state import State


class Ready(State):
    exported_methods = {
        "get_ct",
        "get_grid",
        "get_base_grid",
        "get_bus_demand",
        "get_demand",
        "get_profile",
        "get_hydro",
        "get_grid",
        "get_solar",
        "get_wind",
        "get_gentype_profile",
    } | State.exported_methods

    def __init__(self, scenario):
        """Constructor."""
        super().__init__(scenario)

    def get_ct(self):
        """Returns change table.

        :return: (*dict*) -- change table.
        """
        return copy.deepcopy(self.ct)

    def get_grid(self):
        """Returns Grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        return copy.deepcopy(self.grid)

    def get_base_grid(self):
        """Returns original grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        return Grid(
            self._scenario_info["interconnect"].split("_"),
            source=self._scenario_info["grid_model"],
        )

    def get_profile(self, kind):
        """Returns demand, hydro, solar or wind  profile.

        :param str kind: either *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*pandas.DataFrame*) -- profile.
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        return profile.get_profile(kind)

    def get_hydro(self):
        """Returns hydro profile

        :return: (*pandas.DataFrame*) -- data frame of hydro energy output.
        """
        return self.get_profile("hydro")

    def get_solar(self):
        """Returns solar profile

        :return: (*pandas.DataFrame*) -- data frame of solar energy output.
        """
        return self.get_profile("solar")

    def get_wind(self):
        """Returns wind profile

        :return: (*pandas.DataFrame*) -- data frame of wind energy output.
        """
        return self.get_profile("wind")

    def get_gentype_profile(self, gentype):
        """Returns profile for a generator type.

        :param str gentype: generator type with profile.
        :return: (*pandas.DataFrame*) -- profile.
        :raises ValueError: if ``gentype`` is invalid or not in the grid.
        """
        grid = self.get_grid()
        profile2gen = grid.model_immutables.plants["group_profile_resources"]
        gen2profile = {g: p for p, gs in profile2gen.items() for g in gs}
        if gentype in set(gen2profile):
            if gentype in grid.plant["type"].unique():
                profile = self.get_profile(gen2profile[gentype])
                plant_id = grid.plant.groupby(["type"]).get_group(gentype).index
                return profile[plant_id]
            else:
                raise ValueError(f"No {gentype} in grid")
        else:
            raise ValueError(f"gentype must be one of: {' | '.join(set(gen2profile))}")

    def get_demand(self, original=True):
        """Returns demand profiles.

        :param bool original: should the original demand profile or the
            potentially modified one be returned.
        :return: (*pandas.DataFrame*) -- data frame of demand (hour, zone).
        """
        if not original:
            print("Only original profile is accessible before scenario is complete")
        return self.get_profile("demand")

    def get_bus_demand(self):
        """Returns demand profiles, by bus.

        :return: (*pandas.DataFrame*) -- data frame of demand (hour, bus).
        """
        zone_demand = self.get_demand()
        grid = self.get_grid()
        return distribute_demand_from_zones_to_buses(zone_demand, grid.bus)
