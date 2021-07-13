import copy

from powersimdata.input.input_data import get_bus_demand
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.scenario.state import State


class Ready(State):
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

    def get_hydro(self):
        """Returns hydro profile

        :return: (*pandas.DataFrame*) -- data frame of hydro energy output.
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        return profile.get_profile("hydro")

    def get_solar(self):
        """Returns solar profile

        :return: (*pandas.DataFrame*) -- data frame of solar energy output.
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        return profile.get_profile("solar")

    def get_wind(self):
        """Returns wind profile

        :return: (*pandas.DataFrame*) -- data frame of wind energy output.
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        return profile.get_profile("wind")

    def get_wind_onshore(self):
        """Returns wind onshore profile

        :return: (*pandas.DataFrame*) -- data frame of wind energy output for onshore
            turbines
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        wind = profile.get_profile("wind")

        grid = self.get_grid()
        onshore_id = grid.plant.groupby(["type"]).get_group("wind").index
        return wind[onshore_id]

    def get_wind_offshore(self):
        """Returns wind offshore profile

        :return: (*pandas.DataFrame*) -- data frame of wind energy output for offshore
            turbines
        :raises ValueError: if no offshore wind turbines in grid
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        wind = profile.get_profile("wind")

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
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        return profile.get_profile("demand")

    def get_bus_demand(self):
        """Returns demand profiles, by bus.

        :return: (*pandas.DataFrame*) -- data frame of demand (hour, bus).
        """
        grid = self.get_grid()
        return get_bus_demand(self._scenario_info, grid)
