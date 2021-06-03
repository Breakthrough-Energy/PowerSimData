import warnings

from powersimdata.network.model import area_to_loadzone


def _check_state(scenario):
    """Check if the state of the scenario object is 'analyze'.

    :param powersimdata.scenario.scenario.Scenario scenario:
        scenario instance
    :raise TypeError: if the scenario is not in 'analyze' state.
    """
    if scenario.state.name != "analyze":
        raise TypeError("Scenario state must be 'analyze.'")


class ScenarioInfo:
    """Gather information from previous scenarios for capacity scaling.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance
    :raise TypeError: if the scenario is not in 'analyze' state.
    """

    def __init__(self, scenario):
        _check_state(scenario)
        self.info = scenario.info
        self.pg = scenario.state.get_pg()
        self.grid = scenario.state.get_grid()
        self.demand = scenario.state.get_demand()
        self.grid_model = self.grid.grid_model
        solar = scenario.state.get_solar()
        wind = scenario.state.get_wind()
        hydro = scenario.state.get_hydro()
        self.profile = {"solar": solar, "wind": wind, "hydro": hydro}

    def area_to_loadzone(self, area, area_type=None):
        """Map the query area to a list of loadzones. For more info, see
            :func:`powersimdata.network.model.area_to_loadzone`.

        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*set*) -- set of loadzones associated to the query area
        """
        return area_to_loadzone(self.grid_model, area, area_type)

    def _check_time_range(self, start_time, end_time):
        """Check if the start_time and end_time define a valid time range of
            the given scenario

        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :return: (*tuple*) -- a pair of integer indicates the index of
            the start timestamp and end timestamp in self.pg
        :raise ValueError: if the time range is invalid.
        """
        if (start_time not in self.pg.index) or (end_time not in self.pg.index):
            available_times = "Available time range [%s, %s]" % (
                str(self.pg.index[0]),
                str(self.pg.index[-1]),
            )
            raise ValueError(f"Time range out of scope! {available_times}")
        start_i = self.pg.index.get_loc(start_time)
        end_i = self.pg.index.get_loc(end_time)
        if start_i > end_i:
            raise ValueError("Invalid time range: " "start_time falls behind end_time!")
        return start_i, end_i

    def get_available_resource(self, area, area_type=None):
        """Find the available resources of a specific area in the grid of the
            given scenario

        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*list*) -- a list of available resources in the query area
        """
        loadzone_set = self.area_to_loadzone(area, area_type)
        available_resources = self.grid.plant[
            self.grid.plant["zone_name"].isin(loadzone_set)
        ]["type"].unique()
        return available_resources.tolist()

    def get_demand(self, area, start_time, end_time, area_type=None):
        """Calculate the total demand of the query area during the query time
            range of the given scenario

        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*float*) -- total demand (in MWh)
            based on the specified parameters
        """
        loadzone_set = self.area_to_loadzone(area, area_type)
        self._check_time_range(start_time, end_time)
        total_demand = (
            self.demand.loc[
                start_time:end_time,
                [self.grid.zone2id[loadzone] for loadzone in loadzone_set],
            ]
            .sum()
            .sum()
        )
        return float(total_demand)

    def get_capacity(self, gentype, area, area_type=None):
        """Calculate the total capacity of the query gentype in the query area
            of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*float*) -- total capacity (in MW) based on the
            specified parameters
        """
        loadzone_set = self.area_to_loadzone(area, area_type)
        total_capacity = self.grid.plant[
            (self.grid.plant["type"] == gentype)
            & (self.grid.plant["zone_name"].isin(loadzone_set))
        ]["Pmax"].sum()
        if total_capacity == 0:
            warnings.warn("No such type of generator in the area specified!")
        return float(total_capacity)

    def get_generation(self, gentype, area, start_time, end_time, area_type=None):
        """Calculate the total generation of the query gentype in the query
            area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*float*) -- total generation (in MWh)
            based on the specified parameters
        """
        loadzone_set = self.area_to_loadzone(area, area_type)
        plant_id_list = list(
            self.grid.plant[
                (self.grid.plant["type"] == gentype)
                & (self.grid.plant["zone_name"].isin(loadzone_set))
            ].index
        )
        query_pg_df = self.pg[plant_id_list]
        self._check_time_range(start_time, end_time)
        total_generation = query_pg_df.loc[start_time:end_time].sum().sum()
        return float(total_generation)

    def get_profile_resource(self, gentype, area, start_time, end_time, area_type=None):
        """Calculate the total resource from profile of the query gentype in
            the query area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*float*) -- total resource from profile (in MWh)
            based on the specified parameters
        :raise ValueError: if the resource type is invalid
        """
        loadzone_set = self.area_to_loadzone(area, area_type)
        plant_id_list = list(
            self.grid.plant[
                (self.grid.plant["type"] == gentype)
                & (self.grid.plant["zone_name"].isin(loadzone_set))
            ].index
        )
        if gentype not in self.profile:
            raise ValueError("Invalid resource type")
        query_profile_df = self.profile[gentype][plant_id_list]
        self._check_time_range(start_time, end_time)
        total_resource = query_profile_df.loc[start_time:end_time].sum().sum()
        return float(total_resource)

    def get_curtailment(self, gentype, area, start_time, end_time, area_type=None):
        """Calculate the curtailment of the query gentype in the query
            area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*float*) -- curtailment percentage (rounded up to
            two decimals) based on the specified parameters
        """
        total_generation = self.get_generation(
            gentype, area, start_time, end_time, area_type
        )
        total_profile_resource = self.get_profile_resource(
            gentype, area, start_time, end_time, area_type
        )
        if total_profile_resource == 0 and total_generation == 0:
            return 0
        curtailment = round(1 - (total_generation / total_profile_resource), 4)
        return float(curtailment)

    def get_capacity_factor(self, gentype, area, start_time, end_time, area_type=None):
        """Calculate the capacity factor of the query gentype in the
            query area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*float*) -- capacity factor based on the specified parameters
        :raise ZeroDivisionError: if no generator of gentype is found in the
            area
        """
        start_i, end_i = self._check_time_range(start_time, end_time)
        total_hours = end_i - start_i + 1
        total_capacity = self.get_capacity(gentype, area, area_type)
        if total_capacity == 0:
            raise ZeroDivisionError(
                "No such type of generator in the area " "specified. Division by zero."
            )
        total_generation = self.get_generation(
            gentype, area, start_time, end_time, area_type
        )
        cf = round(total_generation / (total_hours * total_capacity), 4)
        return float(cf)

    def get_no_congest_capacity_factor(
        self, gentype, area, start_time, end_time, area_type=None
    ):
        """Calculate the no congestion capacity factor of the query gentype
            in the query area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str area_type: one of: *'loadzone'*, *'state'*,
            *'state_abbr'*, *'interconnect'*
        :return: (*float*) -- no congestion capacity factor based
            on the specified parameters
        """
        cf = self.get_capacity_factor(gentype, area, start_time, end_time, area_type)
        curtailment = self.get_curtailment(
            gentype, area, start_time, end_time, area_type
        )
        no_congest_cf = round(cf / (1 - curtailment), 4)
        return float(no_congest_cf)
