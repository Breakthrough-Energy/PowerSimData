class AbstractStrategy:
    """
    Base class for strategy objects, contains common functions
    """
    def __init__(self):
        self.targets = {}

    def add_target(self, target):
        """

        :param target:
        :return:
        """
        self.targets[target.name] = target


class IndependentManager(AbstractStrategy):
    """
    Independent strategy manager
    """
    def __init__(self):
        AbstractStrategy.__init__(self)

    def calculate_added_capacities(self, demand):
        """

        :param demand:
        :return:
        """
        pass

    def calculate_next_capacity(self, demand):
        """

        :param demand:
        :return:
        """
        pass


class CollaborativeManager(AbstractStrategy):
    """
    Collaborative strategy manager
    """
    def __init__(self):
        AbstractStrategy.__init__(self)

    def calculate_total_shortfall(self):
        """

        :return:
        """
        total_ce_shortfall = 0
        for tar in self.targets:
            total_ce_shortfall  += self.targets[tar].CE_shortfall
        return total_ce_shortfall

    def calculate_total_prev_ce_generation(self):
        """

        :return:
        """
        total_prev_ce_generation = 0
        for tar in self.targets:
            total_prev_ce_generation += self.targets[tar].calculate_prev_ce_generation()
        return total_prev_ce_generation

    def calculate_added_capacity(self, solar_percentage=None):
        """

        :param solar_percentage:
        :return:
        """
        solar_prev_capacity = self.calculate_total_capacity('solar')
        wind_prev_capacity = self.calculate_total_capacity('wind')

        if solar_percentage is None:
            solar_percentage = solar_prev_capacity/(solar_prev_capacity + wind_prev_capacity)

        ce_shortfall = self.calculate_total_shortfall()
        solar_exp_cap_factor = self.calculate_total_expected_capacity('solar')
        wind_exp_cap_factor = self.calculate_total_expected_capacity('wind')

        if solar_percentage != 0:
            ac_scaling_factor = (1-solar_percentage)/solar_percentage
            solar_added_capacity = 1000/8784*ce_shortfall/(solar_exp_cap_factor+wind_exp_cap_factor*ac_scaling_factor)
            wind_added_capacity = ac_scaling_factor*solar_added_capacity
        else:
            solar_added_capacity = 0
            wind_added_capacity = 1000/8784*ce_shortfall/wind_exp_cap_factor
        return solar_added_capacity, wind_added_capacity

    def calculate_total_capacity(self, category):
        """

        :param category:
        :return:
        """
        total_prev_capacity = 0
        for tar in self.targets:
            total_prev_capacity  += self.targets[tar].resources[category].prev_capacity
        return total_prev_capacity

    def calculate_total_generation(self, category):
        """

        :param category:
        :return:
        """
        total_prev_generation = 0
        for tar in self.targets:
            total_prev_generation  += self.targets[tar].resources[category].prev_generation
        return total_prev_generation

    def calculate_total_capacity_factor(self, category):
        """

        :param category:
        :return:
        """
        total_cap_factor = (self.calculate_total_generation(category) /
                            (self.calculate_total_capacity(category)) * (1000/8784))
        return total_cap_factor

    def calculate_total_expected_capacity(self, category, addl_curtailment=0):
        """

        :param category:
        :param addl_curtailment:
        :return:
        """
        total_exp_cap_factor = self.calculate_total_capacity_factor(category) * (1 - addl_curtailment)
        return total_exp_cap_factor

    def calculate_capacity_scaling(self):
        """

        :return:
        """
        solar_prev_capacity = self.calculate_total_capacity('solar')
        wind_prev_capacity = self.calculate_total_capacity('wind')
        solar_added, wind_added = self.calculate_added_capacity()

        solar_cap_scaling = solar_added/solar_prev_capacity
        wind_cap_scaling = wind_added/wind_prev_capacity
        return solar_cap_scaling, wind_cap_scaling


class TargetManager:

    def __init__(self, name, ce_target_percentage, ce_category, total_demand):
        """

        :param name:
        :param ce_target_percentage:
        :param ce_category:
        :param total_demand:
        """
        self.name = name
        self.CE_category = ce_category

        self.total_demand = total_demand
        self.CE_target_percentage = ce_target_percentage
        self.CE_target = self.total_demand * self.CE_target_percentage

        self.allowed_resources = ['geo', 'solar', 'wind']
        self.resources = {}

        self.CE_shortfall = 0

    def calculate_added_capacity(self, solar_percentage=None):
        """
        Calculate added capacity, maintains solar wind ratio by default
        :param solar_percentage:
        :return: tuple of solar and wind added capacity values
        """
        solar = self.resources['solar']
        wind = self.resources['wind']
        if solar_percentage is None:
            solar_percentage = solar.prev_capacity/(solar.prev_capacity + wind.prev_capacity)
        ce_shortfall = self.CE_shortfall

        if solar_percentage != 0:
            ac_scaling_factor = (1-solar_percentage)/solar_percentage
            solar.added_capacity = 1000/8784*ce_shortfall/(solar.calculate_expected_cap_factor()
                                                           + wind.calculate_expected_cap_factor()*ac_scaling_factor)
            wind.added_capacity = ac_scaling_factor*solar.added_capacity

        else:
            solar.added_capacity = 0
            wind.added_capacity = 1000/8784*ce_shortfall/wind.calculate_expected_cap_factor()

        return solar.added_capacity, wind.added_capacity

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
        :param resource:
        """
        self.resources[resource.name] = resource

    def get_resource(self, resource_name):
        # todo: add error handling
        self.resources[resource_name]

    def calculate_ce_shortfall(self, prev_CE_generation, external_CE_historical_amount):
        """
        Calculates the clean energy shortfall for target area
        :param prev_CE_generation:
        :param external_CE_historical_amount:
        :return:
        """
        if external_CE_historical_amount > prev_CE_generation:
            offset = external_CE_historical_amount
        else:
            offset = prev_CE_generation

        if offset > self.CE_target: 
                CE_shortfall = 0
        else:
            CE_shortfall = self.CE_target - offset

        self.CE_shortfall = CE_shortfall
        return CE_shortfall

    def calculate_ce_overgeneration(self, prev_ce_generation, external_ce_historical_amount):
        """

        :param prev_ce_generation:
        :param external_ce_historical_amount:
        :return:
        """
        if external_ce_historical_amount > prev_ce_generation:
            offset = external_ce_historical_amount
        else:
            offset = prev_ce_generation

        if offset < self.CE_target: 
            ce_overgeneration = 0
        else:
            ce_overgeneration = offset - self.CE_target

        return ce_overgeneration

    def set_allowed_resources(self, allowed_resources):
        """

        :param allowed_resources:
        :return:
        """
        self.allowed_resources =  allowed_resources


class Resource:
    def __init__(self, name, prev_scenario_num):
        self.name = name
        self.prev_scenario_num = prev_scenario_num
        self.no_congestion_cap_factor = 0
        self.prev_capacity = None
        self.prev_cap_factor = None
        self.prev_generation = None
        self.prev_curtailment = None
        self.addl_curtailment = 0

    # todo: calculate directly from scenario results
    def set_capacity(self, no_congestion_cap_factor, prev_capacity, prev_cap_factor):
        """

        :param no_congestion_cap_factor:
        :param prev_capacity:
        :param prev_cap_factor:
        :return:
        """
        self.no_congestion_cap_factor = no_congestion_cap_factor
        self.prev_capacity = prev_capacity
        self.prev_cap_factor = prev_cap_factor

    # todo: calculate directly from scenario results
    def set_generation(self, prev_generation):
        """

        :param prev_generation:
        :return:
        """
        self.prev_generation = prev_generation

    # todo: calculate directly from scenario results
    def set_curtailment(self, prev_curtailment):
        """

        :param prev_curtailment:
        :return:
        """
        self.prev_curtailment = prev_curtailment

    def set_addl_curtailment(self, addl_curtailment):
        """

        :param addl_curtailment:
        :return:
        """
        self.addl_curtailment = addl_curtailment

    def calculate_expected_cap_factor(self):
        """

        :return:
        """
        exp_cap_factor = self.prev_cap_factor * (1-self.addl_curtailment)
        return exp_cap_factor

    def calculate_next_capacity(self, added_capacity):
        """

        :param added_capacity:
        :return:
        """
        next_capacity = self.prev_capacity + added_capacity
        return next_capacity
