import pandas as pd
import jsonpickle
import json
import os
import pickle


class AbstractStrategyManager:
    """
    Base class for strategy objects, contains common functions
    """
    def __init__(self):
        self.targets = {}

    def targets_from_data_frame(self, data_frame):
        for row in data_frame.itertuples():
            self.add_target(TargetManager(row.region_name,
                                          row.ce_target_fraction,
                                          row.ce_category,
                                          row.total_demand,
                                          row.external_ce_historical_amount,
                                          row.solar_percentage))

    def add_target(self, target_manager_obj):
        """
        Add target to strategy object
        :param target_manager_obj: target object to be added
        """
        self.targets[target_manager_obj.region_name] = target_manager_obj

    @staticmethod
    def load_target_from_json(target_name):
        json_file = open(os.path.relpath(os.path.join("save_files", target_name+".json")), "r")
        target_obj = jsonpickle.decode(json_file.read())
        json_file.close()
        return target_obj

    @staticmethod
    def load_target_from_pickle(target_name):
        json_file = open(os.path.relpath(os.path.join("save_files", target_name + ".pkl")), "rb")
        target_obj = pickle.load(json_file)
        json_file.close()
        return target_obj


class IndependentStrategyManager(AbstractStrategyManager):
    """
    Independent strategy manager
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
            solar_added_capacity, wind_added_capacity = self.targets[tar].calculate_added_capacity()
  #          solar_added_capacity, wind_added_capacity = self.targets[tar].calculate_added_capacity_gen_constant()
            target_capacity = [self.targets[tar].region_name,
                               self.targets[tar].resources['solar'].calculate_next_capacity(solar_added_capacity),
                               self.targets[tar].resources['wind'].calculate_next_capacity(wind_added_capacity)]
            target_capacities.append(target_capacity)
        target_capacities_df = pd.DataFrame(target_capacities,
                                            columns=['region_name', 'next_solar_capacity', 'next_wind_capacity'])
        return target_capacities_df


class CollaborativeStrategyManager(AbstractStrategyManager):
    """
    Collaborative strategy manager
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
            total_prev_ce_generation += self.targets[tar].calculate_prev_ce_generation()
        return total_prev_ce_generation

    def calculate_total_added_capacity(self, solar_fraction=None):
        """
        Calculate the capacity to add from total clean energy shortfall
        :param solar_fraction: solar fraction to be used in calculation, default is to maintain from previous result
        :return: solar and wind added capacities
        """
        solar_prev_capacity = self.calculate_total_capacity('solar')
        wind_prev_capacity = self.calculate_total_capacity('wind')

        if solar_fraction is None:
            solar_fraction = solar_prev_capacity / (solar_prev_capacity + wind_prev_capacity)

        ce_shortfall = self.calculate_total_shortfall()
        solar_exp_cap_factor = self.calculate_total_expected_capacity_factor('solar')
        wind_exp_cap_factor = self.calculate_total_expected_capacity_factor('wind')

        if solar_fraction != 0:
            ac_scaling_factor = (1 - solar_fraction) / solar_fraction
            solar_added_capacity = 1000/8784*ce_shortfall/(solar_exp_cap_factor+wind_exp_cap_factor*ac_scaling_factor)
            wind_added_capacity = ac_scaling_factor*solar_added_capacity
        else:
            solar_added_capacity = 0
            wind_added_capacity = 1000/8784*ce_shortfall/wind_exp_cap_factor
        return solar_added_capacity, wind_added_capacity

    def calculate_total_added_capacity_gen_constant(self, solar_fraction=None):
        """
        Calculate the capacity to add from total clean energy shortfall
        :param solar_fraction: solar fraction to be used in calculation, default is to maintain from previous result
        :return: solar and wind added capacities
        """
        solar_prev_capacity = self.calculate_total_capacity('solar')
        wind_prev_capacity = self.calculate_total_capacity('wind')

        if solar_fraction is None:
            solar_fraction = solar_prev_capacity / (solar_prev_capacity + wind_prev_capacity)

        ce_shortfall = self.calculate_total_shortfall()
        solar_exp_cap_factor = self.calculate_total_expected_capacity_factor('solar')
        wind_exp_cap_factor = self.calculate_total_expected_capacity_factor('wind')

        if solar_fraction != 0:
            solar_added_capacity = 1000*ce_shortfall*solar_fraction/(8784*solar_exp_cap_factor)
            wind_added_capacity = 1000*ce_shortfall*(1-solar_fraction)/(8784*wind_exp_cap_factor)
        else:
            solar_added_capacity = 0
            wind_added_capacity = 1000*ce_shortfall/(8784*wind_exp_cap_factor)
        return solar_added_capacity, wind_added_capacity

    def calculate_total_capacity(self, category):
        """
        Calculate total capacity for a resource
        :param category: resource category
        :return: total capacity for a resource
        """
        total_prev_capacity = 0
        for tar in self.targets:
            total_prev_capacity += self.targets[tar].resources[category].prev_capacity
        return total_prev_capacity

    def calculate_total_generation(self, category):
        """
        Calculate total generation for a resource
        :param category: resource category
        :return: total generation for a resource
        """
        total_prev_generation = 0
        for tar in self.targets:
            total_prev_generation += self.targets[tar].resources[category].prev_generation
        return total_prev_generation

    def calculate_total_capacity_factor(self, category):
        """
        Calculate total capacity factor for a target_manager_obj resource
        :param category: resource category
        :return: total capacity factor
        """
        total_cap_factor = (self.calculate_total_generation(category) /
                            (self.calculate_total_capacity(category)) * (1000/8784))
        return total_cap_factor

    def calculate_total_expected_capacity_factor(self, category, addl_curtailment=0):
        """
        Calculate the total expected capacity for a target_manager_obj resource
        :param category: resource category
        :param addl_curtailment: option to add additional curtailment
        :return: total expected capacity factor
        """
        total_exp_cap_factor = self.calculate_total_capacity_factor(category) * (1 - addl_curtailment)
        return total_exp_cap_factor

    def calculate_capacity_scaling(self):
        """
        Calculate the aggregate capacity scaling factor for solar and wind
        :return: solar and wind capacity scaling factors
        """
        solar_prev_capacity = self.calculate_total_capacity('solar')
        wind_prev_capacity = self.calculate_total_capacity('wind')
        solar_added, wind_added = self.calculate_total_added_capacity()
#        solar_added, wind_added = self.calculate_total_added_capacity_gen_constant()

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
            target_capacity = [self.targets[tar].region_name,
                               self.targets[tar].resources['solar'].prev_capacity * solar_scaling,
                               self.targets[tar].resources['wind'].prev_capacity * wind_scaling]
            target_capacities.append(target_capacity)
        target_capacities_df = pd.DataFrame(target_capacities,
                                            columns=['region_name', 'next_solar_capacity', 'next_wind_capacity'])
        return target_capacities_df


class TargetManager:

    def __init__(self, region_name, ce_target_fraction, ce_category, total_demand,
                 external_ce_historical_amount=0, solar_percentage=None):
        """
        Class manages the regional target_manager_obj data and calculations
        :param region_name: region region_name
        :param ce_target_fraction: target_manager_obj fraction for clean energy
        :param ce_category: type of energy target_manager_obj, i.e. renewable, clean energy, etc.
        :param total_demand: total demand for region
        """
        self.region_name = region_name
        self.ce_category = ce_category

        self.total_demand = total_demand
        self.ce_target_fraction = ce_target_fraction
        self.ce_target = self.total_demand * self.ce_target_fraction
        self.external_ce_historical_amount = external_ce_historical_amount
        self.solar_percentage = solar_percentage

        self.allowed_resources = []
        self.resources = {}

    def set_previous_scenario_for_calculation(self, scenario_num):
        pass

    def calculate_added_capacity(self):
        """
        Calculate added capacity, maintains solar wind ratio by default
        :param solar_percentage:
        :return: tuple of solar and wind added capacity values
        """
        solar = self.resources['solar']
        wind = self.resources['wind']
        solar_percentage = self.solar_percentage
        if solar_percentage is None:
            solar_percentage = solar.prev_capacity/(solar.prev_capacity + wind.prev_capacity)
        ce_shortfall = self.calculate_ce_shortfall()

        if solar_percentage != 0:
            ac_scaling_factor = (1-solar_percentage)/solar_percentage
            solar_added_capacity = 1000/8784*ce_shortfall/(solar.calculate_expected_cap_factor()
                                                           + wind.calculate_expected_cap_factor()*ac_scaling_factor)
            wind_added_capacity = ac_scaling_factor*solar_added_capacity

        else:
            solar_added_capacity = 0
            wind_added_capacity = 1000/8784*ce_shortfall/wind.calculate_expected_cap_factor()

        return solar_added_capacity, wind_added_capacity


    def calculate_added_capacity_gen_constant(self):
        """
        Calculate added capacity, maintains solar wind ratio by default
        :param solar_percentage:
        :return: tuple of solar and wind added capacity values
        """
        solar = self.resources['solar']
        wind = self.resources['wind']
        solar_percentage = self.solar_percentage
        if solar_percentage is None:
            solar_percentage = solar.prev_capacity/(solar.prev_capacity + wind.prev_capacity)
        ce_shortfall = self.calculate_ce_shortfall()

        if solar_percentage != 0:
            solar_added_capacity = (ce_shortfall*solar_percentage)/(8784*solar.calculate_expected_cap_factor())
            wind_added_capacity = (ce_shortfall*(1-solar_percentage))/(8784*wind.calculate_expected_cap_factor())

        else:
            solar_added_capacity = 0
            wind_added_capacity = ce_shortfall/8784/wind.calculate_expected_cap_factor()

        return solar_added_capacity, wind_added_capacity


    def calculate_prev_ce_generation(self):
        """
        Calculates total generation from allowed resources
        :return: total generation from allowed resources
        """
        # prev_ce_generation = the sum of all prev_generation in the list of allowed resources
        prev_ce_generation = 0
        for res in self.allowed_resources:
            prev_ce_generation = prev_ce_generation + self.resources[res].prev_generation
        return prev_ce_generation

    def add_resource(self, resource):
        """
        Adds resource to TargetManager
        :param resource: resource to be added
        """
        self.resources[resource.name] = resource

    def get_resource(self, resource_name):
        # todo: add error handling
        return self.resources[resource_name]

    def calculate_ce_shortfall(self):
        """
        Calculates the clean energy shortfall for target_manager_obj area, subtracts the external value if greater than
        total allowed clean energy generation
        :param prev_ce_generation: clean energy generation for allowed resources
        :param external_ce_historical_amount: outside clean energy generation value
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
        Calculates the clean energy overgeneration for target_manager_obj area, subtracts from external value if greater
        than total allowed clean energy generation
        :param prev_ce_generation:
        :param external_ce_historical_amount:
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
        print(os.getcwd())
        json_file = open(os.path.relpath(os.path.join("save_files", self.region_name+".json")), "w")
        obj_json = json.dumps(json.loads(jsonpickle.encode(self)), indent=4, sort_keys=True)
        json_file.write(obj_json)
        json_file.close()

    def save_target_as_pickle(self):
        print(os.getcwd())
        json_file = open(os.path.relpath(os.path.join("save_files", self.region_name+".pkl")), "wb")
        pickle.dump(self, json_file)
        json_file.close()

    def __str__(self):
        return json.dumps(json.loads(jsonpickle.encode(self)), indent=4, sort_keys=True)


class Resource:
    def __init__(self, name, prev_scenario_num):
        # todo: input validation
        self.name = name
        self.prev_scenario_num = prev_scenario_num
        self.no_congestion_cap_factor = None
        self.prev_capacity = None
        self.prev_cap_factor = None
        self.prev_generation = None
        self.prev_curtailment = None
        self.addl_curtailment = 0

    # todo: calculate directly from scenario results
    def set_capacity(self, no_congestion_cap_factor, prev_capacity, prev_cap_factor):
        """
        Sets capacity information for resource
        :param no_congestion_cap_factor: capacity factor with no congestion
        :param prev_capacity: capacity from scenario run
        :param prev_cap_factor: capacity factor from scenario run
        """
        self.no_congestion_cap_factor = no_congestion_cap_factor
        self.prev_capacity = prev_capacity
        self.prev_cap_factor = prev_cap_factor

    # todo: calculate directly from scenario results
    def set_generation(self, prev_generation):
        """
        Set generation from scenario run
        :param prev_generation: generation from scenario run
        """
        self.prev_generation = prev_generation

    # todo: calculate directly from scenario results
    def set_curtailment(self, prev_curtailment):
        """
        Set curtailment from scenario run
        :param prev_curtailment: calculated curtailment from scenario run
        :return:
        """
        self.prev_curtailment = prev_curtailment

    def set_addl_curtailment(self, addl_curtailment):
        """
        Set additional curtailment to included in capacity calculations
        :param addl_curtailment: additional curtailment
        """
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
        return json.dumps(json.loads(jsonpickle.encode(self)), indent=4, sort_keys=True)