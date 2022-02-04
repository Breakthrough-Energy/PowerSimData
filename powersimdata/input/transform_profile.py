import copy

from powersimdata.input.input_data import InputData


class TransformProfile:
    """Transform profile according to operations listed in change table."""

    _default_dates = {"start_date": "2016-01-01 00:00", "end_date": "2016-12-31 23:00"}

    def __init__(self, scenario_info, grid, ct, slice=True):
        """Constructor.

        :param dict scenario_info: scenario information.
        :param powersimdata.input.grid.Grid grid: a Grid object previously
            transformed.
        :param dict ct: change table.
        :param bool slice: whether to slice the profiles by the Scenario's time range.
        """
        self.slice = slice
        self._input_data = InputData()
        self.scenario_info = {**self._default_dates, **scenario_info}

        self.ct = copy.deepcopy(ct)
        self.grid = copy.deepcopy(grid)

        self.scale_keys = {
            "wind": {"wind", "wind_offshore"},
            "solar": {"solar"},
            "hydro": {"hydro"},
            "demand": {"demand"},
        }
        self.n_new_plant, self.n_new_clean_plant = self._get_number_of_new_plant()

    def _get_number_of_new_plant(self):
        """Return the total number of new plant and new plant with profiles.

        :return: (*tuple*) -- first element is the total number of new plant and second
            element is the total number of new clean plant (*hydro*, *solar*,
            *onshore wind* and *offshore wind*).
        """
        n_plant = [0, 0]
        if "new_plant" in self.ct.keys():
            for p in self.ct["new_plant"]:
                n_plant[0] += 1
                if p["type"] in set().union(*self.scale_keys.values()):
                    n_plant[1] += 1
        return n_plant

    def _get_renewable_profile(self, resource):
        """Return the transformed profile.

        :param str resource: *'hydro'*, *'solar'* or *'wind'*.
        :return: (*pandas.DataFrame*) -- power output for generators of specified type
            with plant identification number as columns and UTC timestamp as indices.
        """
        plant_id = (
            self.grid.plant.iloc[: len(self.grid.plant) - self.n_new_plant]
            .isin(self.scale_keys[resource])
            .query("type == True")
            .index
        )

        profile = self._input_data.get_data(self.scenario_info, resource)[plant_id]
        scaled_profile = self._scale_plant_profile(profile)

        if self.n_new_clean_plant > 0:
            new_profile = self._add_plant_profile(profile, resource)
            return scaled_profile.join(new_profile)
        else:
            return scaled_profile

    def _scale_plant_profile(self, profile):
        """Scale profile.

        :param pandas.DataFrame profile: profile with plant identification number as
            columns and UTC timestamp as indices. Values are for 1-W generators.
        :return: (*pandas.DataFrame*) -- scaled power output profile.
        """
        plant_id = list(map(int, profile.columns))
        return profile * self.grid.plant.loc[plant_id, "Pmax"]

    def _add_plant_profile(self, profile, resource):
        """Add profile for plants added via the change table.

        :param pandas.DataFrame profile: profile with plant identification number as
            columns and UTC timestamp as indices.
        :param resource: fuel type.
        :return: (*pandas.DataFrame*) -- profile with additional columns corresponding
            to new generators inserted to the grid via the change table.
        """
        new_plant_ids, neighbor_ids, scaling = [], [], []
        for i, entry in enumerate(self.ct["new_plant"]):
            if entry["type"] in self.scale_keys[resource]:
                new_plant_ids.append(self.grid.plant.index[-self.n_new_plant + i])
                neighbor_ids.append(entry["plant_id_neighbor"])
                scaling.append(entry["Pmax"])

        neighbor_profile = profile[neighbor_ids]
        new_profile = neighbor_profile.multiply(scaling, axis=1)
        new_profile.columns = new_plant_ids
        return new_profile

    def _get_demand_profile(self):
        """Return scaled demand profile.

        :return: (*pandas.DataFrame*) -- data frame of demand.
        """
        zone_id = sorted(self.grid.bus.zone_id.unique())
        demand = self._input_data.get_data(self.scenario_info, "demand").loc[:, zone_id]
        if bool(self.ct) and "demand" in list(self.ct.keys()):
            for key, value in self.ct["demand"]["zone_id"].items():
                print(
                    "Multiply demand in %s (#%d) by %.2f"
                    % (self.grid.id2zone[key], key, value)
                )
                demand.loc[:, key] *= value
        return demand

    def _slice_df(self, df):
        """Return dataframe, sliced by the times specified in scenario_info if and only
        if ``self.slice`` = True.

        :param pandas.DataFrame df: data frame to be sliced.
        :return: (*pandas.DataFrame*) -- sliced data frame.
        """
        if not self.slice:
            return df
        return df.loc[self.scenario_info["start_date"] : self.scenario_info["end_date"]]

    def get_profile(self, name):
        """Return profile.

        :param str name: either *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*pandas.DataFrame*) -- profile.
        :raises ValueError: if argument not one of *'demand'*, *'hydro'*, *'solar'* or
            *'wind'*.
        """
        possible = ["demand", "hydro", "solar", "wind"]
        if name not in possible:
            raise ValueError("Choose from %s" % " | ".join(possible))
        elif name == "demand":
            return self._slice_df(self._get_demand_profile())
        else:
            return self._slice_df(self._get_renewable_profile(name))
