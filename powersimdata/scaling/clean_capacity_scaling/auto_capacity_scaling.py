from powersimdata.scenario.scenario_info import ScenarioInfo
import pandas as pd
import jsonpickle
import json
import os
import pickle


class AbstractStrategyManager:
    """
    Base class for strategy objects, contains common functions
    """
    next_sim_hours = None

    def __init__(self):
        self.targets = {}

    @staticmethod
    def set_next_sim_hours(next_sim_hours):
        """
        Sets the number of hours in the simulation for next capacity
        calculations
        :param int next_sim_hours: number of hours in the simulation
        """
        AbstractStrategyManager.next_sim_hours = next_sim_hours

    def targets_from_data_frame(self, data_frame):
        """
        Bulk creates target objects from dataframe
        """
        for row in data_frame.itertuples():

            if row.solar_percentage == 'None':
                solar_percentage = None
            else:
                solar_percentage = row.solar_percentage
            target = TargetManager(row.region_name,
                                   row.ce_target_fraction,
                                   row.ce_category,
                                   row.total_demand,
                                   row.external_ce_historical_amount,
                                   solar_percentage)
            if row.allowed_resources == '':
                allowed_resources = ['solar', 'wind']
            else:
                split_resources = row.allowed_resources.split(',')
                allowed_resources = [x.strip() for x in split_resources]
            target.set_allowed_resources(allowed_resources)
            self.add_target(target)

    def populate_targets_with_resources(self, scenario_info, start_time,
                                        end_time):
        """
        Add resource objects to all targets with a strategy from a
        specified scenario
        :param powersimdata.scenario.scenario_info.ScenarioInfo scenario_info:
        ScenarioInfo object to calculate scenario resource properties
        :param str start_time: starting datetime for interval of interest
        :param str end_time: ending datetime for interval of interest
        """
        t1 = pd.to_datetime(start_time)
        t2 = pd.to_datetime(end_time)
        assert (t1 < t2), "start_time must be before end_time"
        sim_hours = int((pd.Timedelta(t2 - t1).days + 1) * 24)
        AbstractStrategyManager.next_sim_hours = sim_hours

        for region_name in self.targets:
            print()
            print(region_name)
            print()
            self.targets[region_name].populate_resource_info(scenario_info,
                                                             start_time,
                                                             end_time)

    def add_target(self, target_manager_obj):
        """
        Add target to strategy object
        :param target_manager_obj: target object to be added
        """
        assert (isinstance(target_manager_obj, TargetManager)), \
            "Input must be of TargetManager type"
        self.targets[target_manager_obj.region_name] = target_manager_obj

    @staticmethod
    def load_target_from_json(target_name):
        """
        Loads JSON file of given target
        :param str target_name: name of target to be loaded
        """
        json_file = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "save_files",
            target_name+".json"), "r")
        target_obj = jsonpickle.decode(json_file.read())
        json_file.close()
        return target_obj

    @staticmethod
    def load_target_from_pickle(target_name):
        """
        Loads pickle file of given target
        :param str target_name: name of target to be loaded
        """
        json_file = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "save_files", target_name+".pkl"),
            "rb")
        target_obj = pickle.load(json_file)
        json_file.close()
        return target_obj


class IndependentStrategyManager(AbstractStrategyManager):
    """
    Calculates the next capacities using individual target shortfalls
    """
    def __init__(self):
        AbstractStrategyManager.__init__(self)

    def data_frame_of_next_capacities(self):
        """
        Gathers next target capacity information into a dataframe
        :return: data frame of next target capacities
        """
        target_capacities = []
        for tar in self.targets:
            if self.targets[tar].ce_target_fraction == 0:
                solar_added_capacity, wind_added_capacity = (0, 0)
            else:
                solar_added_capacity, wind_added_capacity =\
                    self.targets[tar].calculate_added_capacity()
            target_capacity = [
                self.targets[tar].region_name,
                self.targets[tar].ce_target_fraction,
                self.targets[tar].ce_target,
                self.targets[tar].calculate_prev_ce_generation(),
                self.targets[tar].calculate_ce_shortfall(),
                solar_added_capacity,
                wind_added_capacity,
                self.targets[tar].resources['solar'].prev_capacity,
                self.targets[tar].resources['wind'].prev_capacity,
                self.targets[tar].resources[
                    'solar'].calculate_expected_cap_factor(),
                self.targets[tar].resources[
                    'wind'].calculate_expected_cap_factor(),
                self.targets[tar].resources[
                    'solar'].calculate_next_capacity(solar_added_capacity),
                self.targets[tar].resources[
                    'wind'].calculate_next_capacity(wind_added_capacity)]
            target_capacities.append(target_capacity)

        target_capacities_df = pd.DataFrame(target_capacities,
                                            columns=[
                                                'region_name',
                                                'ce_target_fraction',
                                                'ce_target',
                                                'previous_ce_generation',
                                                'clean_energy_shortfall',
                                                'solar_added_capacity',
                                                'wind_added_capacity',
                                                'solar_prev_capacity',
                                                'wind_prev_capacity',
                                                'solar_expected_cap_factor',
                                                'wind_expected_cap_factor',
                                                'next_solar_capacity',
                                                'next_wind_capacity'])
        target_capacities_df = target_capacities_df.set_index('region_name')
        return target_capacities_df


class CollaborativeStrategyManager(AbstractStrategyManager):
    """
    Calculates the next capacities using total target shortfalls
    """
    def __init__(self):
        AbstractStrategyManager.__init__(self)

    def calculate_total_shortfall(self):
        """
        Calculate total clean energy shortfall
        :return: total clean energy shortfall
        """
        total_ce_shortfall = 0
        for tar in self.targets:
            total_ce_shortfall += self.targets[tar].calculate_ce_shortfall()
        return total_ce_shortfall

    def calculate_total_prev_ce_generation(self):
        """
        Calculate total allowed clean energy generation
        :return: total allowed clean energy generation
        """
        total_prev_ce_generation = 0
        for tar in self.targets:
            total_prev_ce_generation += \
                self.targets[tar].calculate_prev_ce_generation()
        return total_prev_ce_generation

    def calculate_total_added_capacity(self, solar_fraction=None):
        """
        Calculate the capacity to add from total clean energy shortfall
        :param solar_fraction: solar fraction to be used in calculation,
        default is to maintain from previous result
        :return: solar and wind added capacities
        """
        solar_prev_capacity = self.calculate_total_capacity('solar')
        wind_prev_capacity = self.calculate_total_capacity('wind')

        if solar_fraction is None:
            solar_fraction = solar_prev_capacity / (solar_prev_capacity
                                                    + wind_prev_capacity)

        ce_shortfall = self.calculate_total_shortfall()
        solar_exp_cap_factor = \
            self.calculate_total_expected_capacity_factor('solar')
        wind_exp_cap_factor = \
            self.calculate_total_expected_capacity_factor('wind')

        if solar_fraction != 0:
            ac_scaling_factor = (1 - solar_fraction) / solar_fraction
            solar_added_capacity = \
                ce_shortfall/(AbstractStrategyManager.next_sim_hours*(
                    solar_exp_cap_factor+wind_exp_cap_factor *
                    ac_scaling_factor))
            wind_added_capacity = ac_scaling_factor*solar_added_capacity
        else:
            solar_added_capacity = 0
            wind_added_capacity = \
                ce_shortfall/(AbstractStrategyManager.next_sim_hours *
                              wind_exp_cap_factor)
        return solar_added_capacity, wind_added_capacity

    def calculate_total_added_capacity_gen_constant(self, solar_fraction=None):
        """
        Calculate the capacity to add from total clean energy shortfall
        :param solar_fraction: solar fraction to be used in calculation,
        default is to maintain from previous result
        :return: solar and wind added capacities
        """
        solar_prev_capacity = self.calculate_total_capacity('solar')
        wind_prev_capacity = self.calculate_total_capacity('wind')

        if solar_fraction is None:
            solar_fraction = solar_prev_capacity / \
                             (solar_prev_capacity + wind_prev_capacity)

        ce_shortfall = self.calculate_total_shortfall()
        solar_exp_cap_factor = \
            self.calculate_total_expected_capacity_factor('solar')
        wind_exp_cap_factor = \
            self.calculate_total_expected_capacity_factor('wind')

        if solar_fraction != 0:
            solar_added_capacity = ce_shortfall*solar_fraction/(
                    AbstractStrategyManager.next_sim_hours *
                    solar_exp_cap_factor)
            wind_added_capacity = ce_shortfall*(1-solar_fraction)/(
                    AbstractStrategyManager.next_sim_hours*wind_exp_cap_factor)
        else:
            solar_added_capacity = 0
            wind_added_capacity = \
                ce_shortfall/(AbstractStrategyManager.next_sim_hours *
                              wind_exp_cap_factor)
        return solar_added_capacity, wind_added_capacity

    def calculate_total_capacity(self, category):
        """
        Calculate total capacity for a resource
        :param category: resource category
        :return: total capacity for a resource
        """
        total_prev_capacity = 0
        for tar in self.targets:
            total_prev_capacity += \
                self.targets[tar].resources[category].prev_capacity
        return total_prev_capacity

    def calculate_total_generation(self, category):
        """
        Calculate total generation for a resource
        :param category: resource category
        :return: total generation for a resource
        """
        total_prev_generation = 0
        for tar in self.targets:
            total_prev_generation += \
                self.targets[tar].resources[category].prev_generation
        return total_prev_generation

    def calculate_total_capacity_factor(self, category):
        """
        Calculate total capacity factor for a target_manager_obj resource
        :param category: resource category
        :return: total capacity factor
        """
        # revisit where hourly factor comes from
        total_cap_factor = self.calculate_total_generation(category) / \
            (self.calculate_total_capacity(category)*8784)
        return total_cap_factor

    def calculate_total_expected_capacity_factor(self,
                                                 category,
                                                 addl_curtailment=0):
        """
        Calculate the total expected capacity for a target_manager_obj resource
        :param category: resource category
        :param addl_curtailment: option to add additional curtailment
        :return: total expected capacity factor
        """
        total_exp_cap_factor = \
            self.calculate_total_capacity_factor(category) *\
            (1 - addl_curtailment)
        return total_exp_cap_factor

    def calculate_capacity_scaling(self):
        """
        Calculate the aggregate capacity scaling factor for solar and wind
        :return: solar and wind capacity scaling factors
        """
        solar_prev_capacity = self.calculate_total_capacity('solar')
        wind_prev_capacity = self.calculate_total_capacity('wind')
        solar_added, wind_added = self.calculate_total_added_capacity()

        solar_scaling = (solar_added / solar_prev_capacity) + 1
        wind_scaling = (wind_added / wind_prev_capacity) + 1
        return solar_scaling, wind_scaling

    def data_frame_of_next_capacities(self):
        """
        Gathers next target capacity information into a dataframe
        :return: data frame of next target capacities
        """
        solar_scaling, wind_scaling = self.calculate_capacity_scaling()

        target_capacities = []
        for tar in self.targets:
            target_capacity = [
                self.targets[tar].region_name,
                self.targets[tar].ce_target_fraction,
                self.targets[tar].ce_target,
                self.targets[tar].calculate_prev_ce_generation(),
                self.targets[tar].calculate_ce_shortfall(),
                solar_scaling,
                wind_scaling,
                self.targets[tar].resources['solar'].prev_capacity,
                self.targets[tar].resources['wind'].prev_capacity,
                self.targets[tar].resources[
                    'solar'].prev_capacity * solar_scaling,
                self.targets[tar].resources[
                    'wind'].prev_capacity * wind_scaling]
            target_capacities.append(target_capacity)
        target_capacities_df = pd.DataFrame(target_capacities,
                                            columns=['region_name',
                                                     'ce_target_fraction',
                                                     'ce_target',
                                                     'previous_ce_generation',
                                                     'clean_energy_shortfall',
                                                     'solar_scaling',
                                                     'wind_scaling',
                                                     'solar_prev_capacity',
                                                     'wind_prev_capacity',
                                                     'next_solar_capacity',
                                                     'next_wind_capacity'])
        target_capacities_df = target_capacities_df.set_index('region_name')
        return target_capacities_df


class TargetManager:

    def __init__(self, region_name, ce_target_fraction, ce_category,
                 total_demand, external_ce_historical_amount=0,
                 solar_percentage=None):
        """
        Class manages the regional target_manager_obj data and calculations
        :param region_name: region region_name
        :param ce_target_fraction: target_manager_obj fraction for clean energy
        :param ce_category: type of energy target_manager_obj, i.e. renewable,
        clean energy, etc.
        :param total_demand: total demand for region
        """
        assert (type(region_name) == str), "region_name must be a string"
        assert (type(ce_category) == str), "ce_category must be a string"
        assert (total_demand >= 0), "total_demand must be greater than zero"
        assert (0 <= ce_target_fraction <= 1), "ce_target_fraction must be " \
                                               "between 0 and 1"
        assert (external_ce_historical_amount >= 0), "external_ce_historical" \
                                                     "_amount must be greater"\
                                                     " than zero"
        assert (type(solar_percentage) == float or
                type(solar_percentage) == int or
                solar_percentage is None), "solar_percentage must be" \
                                           " a number or None"
        if type(solar_percentage) == float:
            assert (0 <= solar_percentage <= 1), "solar_percentage must be " \
                                               "between 0 and 1"
        self.region_name = region_name
        self.ce_category = ce_category

        self.total_demand = total_demand
        self.ce_target_fraction = ce_target_fraction
        self.ce_target = self.total_demand * self.ce_target_fraction
        self.external_ce_historical_amount = external_ce_historical_amount
        self.solar_percentage = solar_percentage

        self.allowed_resources = []
        self.resources = {}

    def populate_resource_info(self, scenario_info,
                               start_time, end_time):
        """
        Add resource objects to target using a specified scenario
        :param powersimdata.scenario.scenario_info.ScenarioInfo scenario_info:
        ScenarioInfo object to calculate scenario resource properties
        :param str start_time: starting datetime for interval of interest
        :param str end_time: ending datetime for interval of interest
        """
        allowed_resources = set(self.allowed_resources)
        available_resources = set(
            scenario_info.get_available_resource(self.region_name))
        all_resources = available_resources.union(allowed_resources)

        resources = ResourceManager()
        resources.pull_region_resource_info(self.region_name,
                                            scenario_info,
                                            all_resources,
                                            start_time,
                                            end_time)
        self.add_resource_manager(resources)

    def calculate_added_capacity(self):
        """
        Calculate added capacity, maintains solar wind ratio by default
        :return: tuple of solar and wind added capacity values
        """
        solar = self.resources['solar']
        wind = self.resources['wind']
        solar_percentage = self.solar_percentage
        if solar_percentage is None:
            solar_percentage = solar.prev_capacity/(solar.prev_capacity +
                                                    wind.prev_capacity)
        ce_shortfall = self.calculate_ce_shortfall()

        if solar_percentage != 0:
            ac_scaling_factor = (1-solar_percentage)/solar_percentage
            solar_added_capacity = ce_shortfall/(
                AbstractStrategyManager.next_sim_hours*(
                    solar.calculate_expected_cap_factor() +
                    wind.calculate_expected_cap_factor()*ac_scaling_factor))
            wind_added_capacity = ac_scaling_factor*solar_added_capacity

        else:
            solar_added_capacity = 0
            wind_added_capacity = ce_shortfall/(
                    AbstractStrategyManager.next_sim_hours *
                    wind.calculate_expected_cap_factor())

        return solar_added_capacity, wind_added_capacity

    def calculate_added_capacity_gen_constant(self):
        """
        Calculate added capacity, maintains solar wind ratio by default
        :return: tuple of solar and wind added capacity values
        """
        solar = self.resources['solar']
        wind = self.resources['wind']
        solar_percentage = self.solar_percentage
        if solar_percentage is None:
            solar_percentage = solar.prev_capacity/(solar.prev_capacity
                                                    + wind.prev_capacity)
        ce_shortfall = self.calculate_ce_shortfall()

        if solar_percentage != 0:
            solar_added_capacity = (ce_shortfall*solar_percentage)/(
                    AbstractStrategyManager.next_sim_hours *
                    solar.calculate_expected_cap_factor())
            wind_added_capacity = (ce_shortfall*(1-solar_percentage))/(
                    AbstractStrategyManager.next_sim_hours *
                    wind.calculate_expected_cap_factor())

        else:
            solar_added_capacity = 0
            wind_added_capacity = ce_shortfall /\
                AbstractStrategyManager.next_sim_hours /\
                wind.calculate_expected_cap_factor()

        return solar_added_capacity, wind_added_capacity

    def calculate_prev_ce_generation(self):
        """
        Calculates total generation from allowed resources
        :return: total generation from allowed resources
        """
        # prev_ce_generation = the sum of all prev_generation in the list
        # of allowed resources
        prev_ce_generation = 0
        for res in self.allowed_resources:
            prev_ce_generation = prev_ce_generation + \
                                 self.resources[res].prev_generation
        return prev_ce_generation

    def add_resource(self, resource):
        """
        Adds resource to TargetManager
        :param resource: resource to be added
        """
        assert (isinstance(resource, Resource)),\
            "Input must be of Resource type"
        self.resources[resource.name] = resource

    def add_resource_manager(self, resource_manager):
        assert (isinstance(resource_manager, ResourceManager)),\
            "Input parameter must be an instance of type ResourceManager"
        self.resources = resource_manager

    def calculate_ce_shortfall(self):
        """
        Calculates the clean energy shortfall for target_manager_obj area,
        subtracts the external value if greater than total allowed clean energy
        generation
        :return: clean energy shortfall
        """
        prev_ce_generation = self.calculate_prev_ce_generation()

        if self.external_ce_historical_amount > prev_ce_generation:
            offset = self.external_ce_historical_amount
        else:
            offset = prev_ce_generation

        if offset > self.ce_target:
            ce_shortfall = 0
        else:
            ce_shortfall = self.ce_target - offset

        return ce_shortfall

    def calculate_ce_overgeneration(self):
        """
        Calculates the clean energy overgeneration for target_manager_obj
        area, subtracts from external value if greater than total allowed
        clean energy generation
        :return: clean energy overgeneration
        """
        prev_ce_generation = self.calculate_prev_ce_generation()

        if self.external_ce_historical_amount > prev_ce_generation:
            offset = self.external_ce_historical_amount
        else:
            offset = prev_ce_generation

        if offset < self.ce_target:
            ce_overgeneration = 0
        else:
            ce_overgeneration = offset - self.ce_target

        return ce_overgeneration

    def set_allowed_resources(self, allowed_resources):
        """
        Sets a list of allow resources
        :param allowed_resources: list of allow resources
        """
        # todo: input validation
        self.allowed_resources = allowed_resources

    def save_target_as_json(self):
        """
        Saves target object as indented JSON file named by region name
        """
        print(os.getcwd())
        json_file = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "save_files",
            self.region_name+".json"), "w")
        obj_json = json.dumps(json.loads(jsonpickle.encode(self)), indent=4,
                              sort_keys=True)
        json_file.write(obj_json)
        json_file.close()

    def save_target_as_pickle(self):
        """
        Saves target object as pickle file named by region name
        """
        print(os.getcwd())
        json_file = open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "save_files",
            self.region_name+".pkl"), "wb")
        pickle.dump(self, json_file)
        json_file.close()

    def __str__(self):
        """
        Outputs indented JSON string af object properties
        """
        return json.dumps(
            json.loads(jsonpickle.encode(self, unpicklable=False)),
            indent=4,
            sort_keys=True)


class ResourceManager:
    """
    Class manages the creation of resource objects from scenario information
    """
    def __init__(self):
        self.resources = {}

    def __getitem__(self, key):
        """
        Allows indexing into the resources dictionary directly from the
        object variable, i.e. res = ResourceManager; res["solar"] is the
        same as res.resources["solar"]
        """
        try:
            return self.resources[key]
        except KeyError as e:
            print(e)

    def pull_region_resource_info(self, region_name, scenario_info,
                                  region_resources, start_time, end_time):
        """
        Pulls resource information from scenario info object over the
        specified time range
        :param str region_name: name of region to extract from scenario
        :param powersimdata.scenario.scenario_info.ScenarioInfo scenario_info:
        ScenarioInfo object to calculate scenario resource properties
        :param set region_resources: resources to extract from scenario
        :param str start_time: starting time for simulation
        :param str end_time: ending time for simulation
        """
        assert (isinstance(scenario_info, ScenarioInfo)),\
            "input parameter must be an instance of type ScenarioInfo"

        for resource_name in region_resources:
            resource_obj = Resource(resource_name,
                                    int(scenario_info.info['id']))

            prev_capacity = scenario_info.get_capacity(resource_name,
                                                       region_name)

            if prev_capacity == 0:
                prev_cap_factor = 0
                print('No existing resource ' + resource_name + '!')
            else:
                prev_cap_factor = scenario_info.get_capacity_factor(
                    resource_name,
                    region_name,
                    start_time,
                    end_time)

            prev_generation = scenario_info.get_generation(
                resource_name,
                region_name,
                start_time,
                end_time)

            try:
                prev_curtailment = scenario_info.get_curtailment(
                    resource_name,
                    region_name,
                    start_time,
                    end_time)
            except Exception as e:
                print(e)
                prev_curtailment = 0

            try:
                no_congestion_cap_factor =\
                    scenario_info.get_no_congest_capacity_factor(
                        resource_name,
                        region_name,
                        start_time,
                        end_time)
            except Exception as e:
                print(e)
                no_congestion_cap_factor = 0

            resource_obj.set_capacity(
                no_congestion_cap_factor,
                prev_capacity,
                prev_cap_factor
            )
            resource_obj.set_generation(prev_generation)
            resource_obj.set_curtailment(prev_curtailment)

            self.resources[resource_name] = resource_obj
            print('Added resource ' + resource_name + '!')
            print()


class Resource:
    def __init__(self, name, prev_scenario_num):
        assert (type(name) == str), "name must be a string"
        assert (type(prev_scenario_num) == int), \
            "prev_scenario_num must be and integer"
        self.name = name
        self.prev_scenario_num = prev_scenario_num
        self.no_congestion_cap_factor = None
        self.prev_capacity = None
        self.prev_cap_factor = None
        self.prev_generation = None
        self.prev_curtailment = None
        self.addl_curtailment = 0

    # todo: calculate directly from scenario results
    def set_capacity(self, no_congestion_cap_factor, prev_capacity,
                     prev_cap_factor):
        """
        Sets capacity information for resource
        :param no_congestion_cap_factor: capacity factor with no congestion
        :param prev_capacity: capacity from scenario run
        :param prev_cap_factor: capacity factor from scenario run
        """
        assert (0 <= no_congestion_cap_factor <= 1), \
            "no_congestion_cap_factor must be between 0 and 1"
        assert (0 <= prev_cap_factor <= 1), \
            "prev_cap_factor must be between 0 and 1"
        assert (prev_capacity >= 0), "prev_capacity must be greater than zero"

        self.no_congestion_cap_factor = no_congestion_cap_factor
        self.prev_capacity = prev_capacity
        self.prev_cap_factor = prev_cap_factor

    # todo: calculate directly from scenario results
    def set_generation(self, prev_generation):
        """
        Set generation from scenario run
        :param prev_generation: generation from scenario run
        """
        assert (prev_generation >= 0), \
            "prev_generation must be greater than zero"
        self.prev_generation = prev_generation

    # todo: calculate directly from scenario results
    def set_curtailment(self, prev_curtailment):
        """
        Set curtailment from scenario run
        :param prev_curtailment: calculated curtailment from scenario run
        :return:
        """
        assert (prev_curtailment >= 0), \
            "prev_curtailment must be greater than zero"
        self.prev_curtailment = prev_curtailment

    def set_addl_curtailment(self, addl_curtailment):
        """
        Set additional curtailment to included in capacity calculations
        :param addl_curtailment: additional curtailment
        """
        assert (addl_curtailment >= 0), \
            "addl_curtailment must be greater than zero"
        self.addl_curtailment = addl_curtailment

    def calculate_expected_cap_factor(self):
        """
        Calculates the capacity factor including additional curtailment
        :return: capacity factor for resource
        """
        exp_cap_factor = self.prev_cap_factor * (1-self.addl_curtailment)
        return exp_cap_factor

    def calculate_next_capacity(self, added_capacity):
        """
        Calculates next capacity to be used for scenario
        :param added_capacity: calculated added capacity
        :return: next capacity to be used for scenario
        """
        next_capacity = self.prev_capacity + added_capacity
        return next_capacity

    def __str__(self):
        """
        Outputs indented JSON string af object properties
        """
        return json.dumps(json.loads(jsonpickle.encode(self,
                                                       unpicklable=False
                                                       )),
                          indent=4, sort_keys=True)
