import warnings

from prereise.gather.constants import abv2state, state2loadzone, \
    interconnect2loadzone


def _check_state(scenario):
    """Check if the state of the scenario object is 'analyze'.

    :param powersimdata.scenario.scenario.Scenario scenario:
        scenario instance
    :raise Exception: if the scenario is not in 'analyze' state.
    """
    if scenario.state.name != 'analyze':
        raise Exception('Scenario state must be \'analyze.\'')


class ScenarioInfo:
    """Gather information from previous scenarios for capacity scaling.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance
    :raise Exception: if the scenario is not in 'analyze' state.
    """
    def __init__(self, scenario):
        _check_state(scenario)
        self.pg = scenario.state.get_pg()
        self.grid = scenario.state.get_grid()
        self.demand = scenario.state.get_demand()
        solar = scenario.state.get_solar()
        wind = scenario.state.get_wind()
        hydro = scenario.state.get_hydro()
        self.profile = {
            'solar': solar,
            'wind': wind,
            'hydro': hydro
        }

    def area_to_loadzone(self, area):
        """Map the query area to a list of loadzones

        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :return: (*set*) -- set of loadzones associated to the query area
        :raise Exception: if area is invalid.
        """
        if area in self.grid.zone2id:
            loadzone_set = {area}
        elif area in abv2state:
            loadzone_set = state2loadzone[abv2state[area]]
        elif area in list(abv2state.values()):
            loadzone_set = state2loadzone[area]
        elif area in {'Texas', 'Western', 'Eastern'}:
            loadzone_set = interconnect2loadzone[area]
        elif area == 'all':
            loadzone_set = set(self.grid.zone2id.keys())
        else:
            print("%s is incorrect." % area)
            raise ValueError('Invalid area')
        return loadzone_set

    def check_time_range(self, start_time, end_time):
        """Check if the start_time and end_time define a valid time range of
            the given scenario

        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :return: (*tuple*) -- a pair of integer indicates the index of
            the start timestamp and end timestamp in self.pg
        :raise Exception: if the time range is invalid.
        """
        if (start_time not in self.pg.index) or \
                (end_time not in self.pg.index):
            print('Available time range [%s, %s]' % (str(self.pg.index[0]),
                                                     str(self.pg.index[-1])))
            raise ValueError('Time range out of scope!')
        start_i = self.pg.index.get_loc(start_time)
        end_i = self.pg.index.get_loc(end_time)
        if start_i > end_i:
            raise ValueError('Invalid time range: '
                             'start_time falls behind end_time!')
        return start_i, end_i

    def get_available_resource(self, area):
        """Find the available resources of a specific area in the grid of the
            given scenario

        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :return: (*list*) -- a list of available resources in the query area
        """
        loadzone_set = self.area_to_loadzone(area)
        available_resources = self.grid.plant[
            self.grid.plant['zone_name'].isin(loadzone_set)]['type'].unique()
        return available_resources.tolist()

    def get_demand(self, area, start_time, end_time):
        """Calculate the total demand of the query area during the query time
            range of the given scenario

        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :return: (*float*) -- total demand (in MWh)
            based on the specified parameters
        """
        loadzone_set = self.area_to_loadzone(area)
        self.check_time_range(start_time, end_time)
        total_demand = self.demand.loc[
            start_time:end_time,
            [self.grid.zone2id[loadzone]
             for loadzone in loadzone_set]
        ].sum().sum()
        return float(total_demand)

    def get_capacity(self, gentype, area):
        """Calculate the total capacity of the query gentype in the query area
            of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :return: (*float*) -- total capacity (in MW) based on the
            specified parameters
        """
        loadzone_set = self.area_to_loadzone(area)
        total_capacity = self.grid.plant[
            (self.grid.plant['type'] == gentype) &
            (self.grid.plant['zone_name'].isin(loadzone_set))]['Pmax'].sum()
        if total_capacity == 0:
            warnings.warn('No such type of generator in the area specified!')
        return float(total_capacity)

    def get_generation(self, gentype, area, start_time, end_time):
        """Calculate the total generation of the query gentype in the query
            area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :return: (*float*) -- total generation (in MWh)
            based on the specified parameters
        """
        loadzone_set = self.area_to_loadzone(area)
        plant_id_list = list(self.grid.plant
                             [(self.grid.plant['type'] == gentype) &
                              (self.grid.plant['zone_name'].
                               isin(loadzone_set))].index)
        query_pg_df = self.pg[plant_id_list]
        self.check_time_range(start_time, end_time)
        total_generation = query_pg_df.loc[start_time:end_time].sum().sum()
        return float(total_generation)

    def get_profile_resource(self, gentype, area, start_time, end_time):
        """Calculate the total resource from profile of the query gentype in
            the query area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :return: (*float*) -- total resource from profile (in MWh)
            based on the specified parameters
        :raise Exception: if the resource type is invalid
        """
        loadzone_set = self.area_to_loadzone(area)
        plant_id_list = list(self.grid.plant
                             [(self.grid.plant['type'] == gentype) &
                              (self.grid.plant['zone_name'].
                               isin(loadzone_set))].index)
        if gentype not in self.profile:
            raise ValueError('Invalid resource type')
        query_profile_df = self.profile[gentype][plant_id_list]
        self.check_time_range(start_time, end_time)
        total_resource = query_profile_df.loc[start_time:end_time].sum().sum()
        return float(total_resource)

    def get_curtailment(self, gentype, area, start_time, end_time):
        """Calculate the curtailment of the query gentype in the query
            area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :return: (*float*) -- curtailment percentage (rounded up to
            two decimals) based on the specified parameters
        """
        total_generation = self.get_generation(gentype, area,
                                               start_time, end_time)
        total_profile_resource = self.get_profile_resource(gentype, area,
                                                           start_time,
                                                           end_time)
        if total_profile_resource == 0 and total_generation == 0:
            return 0
        curtailment = round(1 - (total_generation / total_profile_resource), 4)
        return float(curtailment)

    def get_capacity_factor(self, gentype, area, start_time, end_time):
        """Calculate the capacity factor of the query gentype in the
            query area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :return: (*float*) -- capacity factor based on the specified parameters
        """
        start_i, end_i = self.check_time_range(start_time, end_time)
        total_hours = end_i - start_i + 1
        total_capacity = self.get_capacity(gentype, area)
        if total_capacity == 0:
            raise ZeroDivisionError('No such type of generator in the area '
                                    'specified. Division by zero.')
        total_generation = self.get_generation(gentype, area,
                                               start_time, end_time)
        cf = round(total_generation / (total_hours * total_capacity), 4)
        return float(cf)

    def get_no_congest_capacity_factor(self, gentype, area,
                                       start_time, end_time):
        """Calculate the no congestion capacity factor of the query gentype
            in the query area during the query time range of the given scenario

        :param str gentype: type of generator
        :param str area: one of: *loadzone*, *state*, *state abbreviation*,
            *interconnect*, *'all'*
        :param str start_time: start timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :param str end_time: end timestamp in the format
            *'YYYY-MM-DD HH:MM:SS'*
        :return: (*float*) -- no congestion capacity factor based
            on the specified parameters
        """
        cf = self.get_capacity_factor(gentype, area, start_time, end_time)
        curtailment = self.get_curtailment(gentype, area, start_time, end_time)
        no_congest_cf = round(cf / (1 - curtailment), 4)
        return float(no_congest_cf)
