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
        "get_hydro",
        "get_grid",
        "get_solar",
        "get_wind",
        "get_wind_offshore",
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

    def get_wind_onshore(self):
        """Returns wind onshore profile

        :return: (*pandas.DataFrame*) -- data frame of wind energy output for onshore
            turbines
        """
        wind = self.get_profile("wind")
        grid = self.get_grid()
        onshore_id = grid.plant.groupby(["type"]).get_group("wind").index
        return wind[onshore_id]

    def get_wind_offshore(self):
        """Returns wind offshore profile

        :return: (*pandas.DataFrame*) -- data frame of wind energy output for offshore
            turbines
        :raises ValueError: if no offshore wind turbines in grid
        """
        wind = self.get_profile("wind")
        grid = self.get_grid()
        if "wind_offshore" in grid.plant["type"].unique():
            offshore_id = grid.plant.groupby(["type"]).get_group("wind_offshore").index
            return wind[offshore_id]
        else:
            raise ValueError("No offshore wind turbines in grid")

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
