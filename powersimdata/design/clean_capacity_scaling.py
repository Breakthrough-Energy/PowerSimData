import jsonpickle
import json
import os
import pickle

import numpy as np
import pandas as pd

from powersimdata.design.scenario_info import ScenarioInfo, area_to_loadzone
from powersimdata.design.mimic_grid import mimic_generation_capacity
from powersimdata.input.grid import Grid


def _check_solar_fraction(solar_fraction):
    """Checks that the solar_fraction is between 0 and 1, or is None.

    :param float scale_fraction: desired solar fraction for new capacity.
    :raises TypeError: if type is not int, float, or None.
    :raises ValueError: if value is not between 0 and 1.
    """
    if solar_fraction is None:
        pass
    elif isinstance(solar_fraction, (int, float)):
        if not (0 <= solar_fraction <= 1):
            raise ValueError("solar_fraction must be between 0 and 1")
    else:
        raise TypeError("solar_fraction must be int/float or None")


def _apply_zone_scale_factor_to_ct(ct, fuel, zone_id, scale_factor):
    """Applies a zone scaling factor to a change table, creating internal
    change table structure as necessary. New keys are added, existing keys are
    multiplied.

    :param dict ct: a dictionary of scale factors, with structure matching
        ct from powersimdata.input.change_table.ChangeTable.
    :param str fuel: the fuel to be scaled.
    :param int zone_id: the zone_id to be scaled.
    :param int/float scale_factor: how much the zone should be scaled up by.
    """
    if fuel not in ct:
        ct[fuel] = {}
    if "zone_id" not in ct[fuel]:
        ct[fuel]["zone_id"] = {}
    if zone_id not in ct[fuel]["zone_id"]:
        ct[fuel]["zone_id"][zone_id] = scale_factor
    else:
        ct[fuel]["zone_id"][zone_id] *= scale_factor


def load_targets_from_csv(filename):
    """Interprets a CSV file as a set of targets, ensuring that required columns are present,
    and filling in default values for optional columns.

    :param str filename: filepath to targets csv.
    :return: (*pandas.DataFrame*) -- DataFrame of targets from csv file
    :raises TypeError: if filename is not a string
    :raises ValueError: if one or more required columns is missing.
    """
    # Constants
    mandatory_columns = {
        "region_name",
        "ce_target_fraction",
    }
    optional_column_defaults = {
        "allowed_resources": "solar, wind",
        "external_ce_addl_historical_amount": 0,
        "solar_percentage": np.nan,
    }

    # Validate input
    if not isinstance(filename, str):
        raise TypeError("filename must be a str")
    # Interpret as object so that we can fillna() with a mixed-type dict
    raw_targets = pd.read_csv(filename).astype(object)
    raw_columns = set(raw_targets.columns)
    if not mandatory_columns <= raw_columns:
        missing_columns = mandatory_columns - raw_columns
        raise ValueError(f'Missing columns: {", ".join(missing_columns)}')
    raw_targets.set_index("region_name", inplace=True)
    # Report which columns are used vs. unused
    ignored_columns = raw_columns - mandatory_columns - optional_column_defaults.keys()
    print(f"ignoring: {ignored_columns}")

    for column in optional_column_defaults.keys():
        # Fill optional columns that are missing entirely
        if column not in raw_columns:
            raw_targets[column] = np.nan
    # Fill any empty cells within optional columns
    raw_targets.fillna(value=optional_column_defaults, inplace=True)

    return raw_targets


def _make_zonename2target(grid, targets, enforced_area_type=None):
    """Creates a dictionary of {zone_name: target_name} pairs.

    :param powersimdata.input.grid.Grid grid: Grid instance defining the set of zones.
    :param iterable targets: a collection of strings, used to look up constituent zones.
    :param str/None enforced_area_type: if provided, specify to area_to_loadzone()
        that the area type must be this. If None, area_to_loadzone() proceeds in order.
    :return: (*dict*) -- a dictionary of {zone_name: target_name} pairs.
    """
    target_zones = {
        target_name: area_to_loadzone(grid, target_name, area_type=enforced_area_type)
        for target_name in targets
    }
    zonename2target = {}
    for target_name, zone_set in target_zones.items():
        # Filter out parts of states not in this interconnect
        filtered_zone_set = zone_set & set(grid.zone2id.keys())
        zonename2target.update({zone: target_name for zone in filtered_zone_set})
    untargetted_zones = set(grid.zone2id.keys()) - set(zonename2target.keys())
    if len(untargetted_zones) > 0:
        err_msg = f"Targets do not cover all load zones. Missing: {untargetted_zones}"
        raise ValueError(err_msg)
    return zonename2target


def _get_scenario_length(scenario):
    """Get the number of hours in a scenario.
    :param powersimdata.scenario.scenario.Scenario scenario: A Scenario instance.
    :return: (*int*) -- the number of hours in the scenario.
    """

    if scenario.state.name == "create":
        start_ts = pd.Timestamp(scenario.state.builder.start_date)
        end_ts = pd.Timestamp(scenario.state.builder.end_date)
    else:
        start_ts = pd.Timestamp(scenario.info["start_date"])
        end_ts = pd.Timestamp(scenario.info["end_date"])
    num_hours = (end_ts - start_ts) / pd.Timedelta(hours=1) + 1
    return num_hours


def add_resource_data_to_targets(input_targets, scenario, enforced_area_type=None):
    """Add resource data to targets. This data includes: previous capacity,
    previous generation, previous capacity factor (with and without curtailment),
    and previous curtailment.
    :param pandas.DataFrame input_targets: table includeing target names, used to
        summarize resource data.
    :param powersimdata.scenario.scenario.Scenario scenario: A Scenario instance.
    :param str/None enforced_area_type: if provided, specify to area_to_loadzone()
        that the area type must be this. If None, area_to_loadzone() proceeds in order.
    :return: (*pandas.DataFrame*) -- DataFrame of targets including resource data.
    """
    targets = input_targets.copy()
    grid = scenario.state.get_grid()
    plant = grid.plant
    curtailment_types = ["hydro", "solar", "wind"]
    scenario_length = _get_scenario_length(scenario)

    # Map each zone in the grid to a target
    targets_list = input_targets.index.tolist()
    zonename2target = _make_zonename2target(grid, targets_list, enforced_area_type)
    plant["target_area"] = [zonename2target[z] for z in plant["zone_name"]]

    # Summarize important values by target area & type
    groupby_cols = [plant.target_area, plant.type]
    # Capacity
    capacity_groupby = plant.Pmax.groupby(groupby_cols)
    capacity_by_target_type = capacity_groupby.sum().unstack(fill_value=0)
    # Generated energy
    pg_groupby = scenario.state.get_pg().sum().groupby(groupby_cols)
    summed_generation = pg_groupby.sum().unstack(fill_value=0)
    # Calculate: capacity factors, curtailment, no_curtailment_cap_factor
    # Hydro and solar are straightforward
    hydro_plant_sum = scenario.state.get_hydro().sum()
    hydro_plant_targets = plant[plant.type == "hydro"].target_area
    hydro_potential_by_target = hydro_plant_sum.groupby(hydro_plant_targets).sum()
    solar_plant_sum = scenario.state.get_solar().sum()
    solar_plant_targets = plant[plant.type == "solar"].target_area
    solar_potential_by_target = solar_plant_sum.groupby(solar_plant_targets).sum()
    # Wind is a little tricker because get_wind() returns 'wind' and 'wind_offshore'
    onshore_wind_plants = plant[plant.type == "wind"].index
    onshore_wind_plant_sum = scenario.state.get_wind().sum()[onshore_wind_plants]
    wind_plant_targets = plant[plant.type == "wind"].target_area
    wind_potential_by_target = onshore_wind_plant_sum.groupby(wind_plant_targets).sum()
    potentials_series = [
        hydro_potential_by_target,
        solar_potential_by_target,
        wind_potential_by_target,
    ]
    potential = pd.concat(potentials_series, axis=1)
    possible_energy = scenario_length * capacity_by_target_type[curtailment_types]
    capacity_factor = summed_generation[curtailment_types] / possible_energy
    curtailment = (potential - summed_generation[curtailment_types]) / possible_energy
    no_curtailment_cap_factor = potential / possible_energy
    # Now add these calculations to
    total_capacity = capacity_by_target_type.sum()
    nonzero_capacity_resources = total_capacity[total_capacity > 0].index.tolist()
    for r in nonzero_capacity_resources:
        targets[f"{r}.prev_capacity"] = capacity_by_target_type[r]
        targets[f"{r}.prev_generation"] = summed_generation[r]
        if r in curtailment_types:
            targets[f"{r}.prev_cap_factor"] = capacity_factor[r]
            targets[f"{r}.no_curtailment_cap_factor"] = no_curtailment_cap_factor[r]
            targets[f"{r}.curtailment"] = curtailment[r]
            targets[f"{r}.addl_curtailment"] = 0

    return targets


def add_demand_to_targets(input_targets, scenario, enforced_area_type=None):
    """Add demand data to targets.
    :param pandas.DataFrame input_targets: table including target names, used to
        summarize demand.
    :param powersimdata.scenario.scenario.Scenario scenario: A Scenario instance.
    :param str/None enforced_area_type: if provided, specify to area_to_loadzone()
        that the area type must be this. If None, area_to_loadzone() proceeds in order.
    :return: (*pandas.DataFrame*) -- DataFrame of targets including demand data.
    """
    grid = scenario.state.get_grid()
    targets = input_targets.copy()

    zonename2target = _make_zonename2target(grid, targets.index, enforced_area_type)
    zoneid2target = {grid.zone2id[z]: target for z, target in zonename2target.items()}
    summed_demand = scenario.state.get_demand().sum().to_frame()
    summed_demand["target"] = [zoneid2target[id] for id in summed_demand.index]
    targets["demand"] = summed_demand.groupby("target").sum()
    return targets


def add_shortfall_to_targets(input_targets):
    """Add shortfall data to targets.
    :param pandas.DataFrame input_targets: table with demand, prev_generation,
        and ce_target_fraction.
    :return: (*pandas.DataFrame*) -- DataFrame of targets including shortfall data.
    """
    targets = input_targets.copy()
    allowed_resources_dict = targets.allowed_resources.to_dict()
    allowed_sets = {
        target: {resource.strip() for resource in allowed.split(",")}
        for target, allowed in allowed_resources_dict.items()
    }
    # Detect if there are allowed resources that aren't in the grid, and add them
    all_allowed = set().union(*allowed_sets.values())
    for resource in all_allowed:
        if f"{resource}.prev_generation" not in targets.columns:
            targets[f"{resource}.prev_generation"] = 0
    targets["prev_ce_generation"] = targets.apply(
        lambda x: sum([x[f"{r}.prev_generation"] for r in allowed_sets[x.name]]), axis=1
    )
    targets["ce_target"] = targets.demand * targets.ce_target_fraction
    total_ce_generation = (
        targets.prev_ce_generation + targets.external_ce_addl_historical_amount
    )
    raw_shortfall = targets.ce_target - total_ce_generation
    targets["ce_shortfall"] = raw_shortfall.clip(lower=0)
    targets["ce_overgeneration"] = (-1 * raw_shortfall).clip(lower=0)
    return targets


def add_new_capacities_independent(input_targets, scenario_length):
    """Calculates new capacities based on an Independent strategy.
    :param pandas.DataFrame input_targets: table of targets.
    :param int scenario_length: number of hours in new scenario.
    :return: (*pandas.DataFrame*) -- targets dataframe with next capacities added.
    """

    def calculate_added_capacity(target):
        if pd.isnull(target["solar_percentage"]):
            new_solar_percentage = target["solar.prev_capacity"] / (
                target["solar.prev_capacity"] + target["wind.prev_capacity"]
            )
        else:
            new_solar_percentage = target["solar_percentage"]
        new_wind_percentage = 1 - new_solar_percentage
        solar_expected_cf = target["solar.prev_cap_factor"] * (
            1 - target["solar.addl_curtailment"]
        )
        wind_expected_cf = target["wind.prev_cap_factor"] * (
            1 - target["wind.addl_curtailment"]
        )
        if np.isnan(solar_expected_cf):
            avg_new_cf = wind_expected_cf * new_wind_percentage
        elif np.isnan(wind_expected_cf):
            avg_new_cf = solar_expected_cf * new_solar_percentage
        else:
            avg_new_cf = (
                solar_expected_cf * new_solar_percentage
                + wind_expected_cf * new_wind_percentage
            )
        total_new_capacity = target["ce_shortfall"] / (avg_new_cf * scenario_length)
        new_solar = total_new_capacity * new_solar_percentage
        new_wind = total_new_capacity * (1 - new_solar_percentage)
        return new_solar, new_wind

    targets = input_targets.copy()
    if addl_curtailment is not None:
        addl_curtailment.columns = [
            f"{r}.addl_curtailment" for r in addl_curtailment.columns
        ]
    targets = targets.join(addl_curtailment)
    # Calculate new capacity
    new_solar_wind = targets.apply(
        calculate_added_capacity, result_type="expand", axis=1
    )
    # Add new capacity to targets dataframe
    new_solar_wind.columns = ["solar.added_capacity", "wind.added_capacity"]
    targets = pd.concat([targets, new_solar_wind], axis=1)
    for r in ("solar", "wind"):
        targets[f"{r}.next_capacity"] = (
            targets[f"{r}.prev_capacity"] + targets[f"{r}.added_capacity"]
        )
    return targets


def add_new_capacities_collaborative(
    input_targets, scenario_length, solar_fraction=None, addl_curtailment=None
):
    """Calculates new capacities based on a Collaborative strategy.
    :param pandas.DataFrame input_targets: table of targets.
    :param int scenario_length: number of hours in new scenario.
    :param float/None solar_fraction: how much new capacity should be solar.
        If given None, maintain previous ratio.
    :param dict/None addl_curtailment: how much new curtailment is expected, by resource.
        If given None, assume zero.
    :return: (*pandas.DataFrame*) -- targets dataframe with next capacities added.
    """
    targets = input_targets.copy()
    new_resources = ("solar", "wind")

    participating_targets = targets[targets.ce_target > 0]
    participating_capacity = pd.Series(
        {
            resource: participating_targets[f"{resource}.prev_capacity"].sum()
            for resource in new_resources
        }
    )
    participating_generation = pd.Series(
        {
            resource: participating_targets[f"{resource}.prev_generation"].sum()
            for resource in new_resources
        }
    )
    participating_cap_factor = participating_generation / (
        participating_capacity * scenario_length
    )
    if addl_curtailment is None:
        addl_curtailment = {resource: 0 for resource in new_resources}
    expected_cf = participating_cap_factor * (1 - pd.Series(addl_curtailment))
    if solar_fraction is None:
        solar_fraction = participating_capacity["solar"] / participating_capacity.sum()
    avg_new_cf = (expected_cf["solar"] * solar_fraction) + (
        expected_cf["wind"] * (1 - solar_fraction)
    )
    summed_shortfall = participating_targets.ce_shortfall.sum()
    summed_overgeneration = participating_targets.ce_overgeneration.sum()
    overall_shortfall = summed_shortfall - summed_overgeneration
    total_new_capacity = overall_shortfall / (avg_new_cf * scenario_length)
    new_type_capacity = pd.Series(
        {
            "solar": total_new_capacity * solar_fraction,
            "wind": total_new_capacity * (1 - solar_fraction),
        }
    )
    scaling_factors = 1 + new_type_capacity / participating_capacity
    for r in ("solar", "wind"):
        # Fill non-participating targets with previous capacity
        targets[f"{r}.next_capacity"] = targets[f"{r}.prev_capacity"]
        # Scale participating targets
        targets.loc[targets.ce_target > 0, f"{r}.next_capacity"] = (
            targets.loc[targets.ce_target > 0, f"{r}.prev_capacity"]
            * scaling_factors[r]
        )
    return targets


def create_change_table(input_targets, ref_scenario):
    """Using a reference scenario, create a change table which scales all
    plants in a base grid to capacities matching the reference grid, with
    the exception of wind and solar plants which are scaled up according to
    the clean capacity scaling logic.

    :param pandas.DataFrame input_targets: table of targets, with previous and
        next capacities.
    :param powersimdata.scenario.scenario.Scenario ref_scenario: reference scenario
        to mimic.
    :return: (*dict*) -- dictionary to be passed to a change table.
    """
    epsilon = 1e-3
    interconnect = ref_scenario.info["interconnect"]
    base_grid = Grid([interconnect])
    grid_zones = base_grid.plant.zone_name.unique()
    ref_grid = ref_scenario.state.get_grid()
    ct = mimic_generation_capacity(base_grid, ref_grid)
    for region in input_targets.index:
        prev_solar = input_targets.loc[region, "solar.prev_capacity"]
        prev_wind = input_targets.loc[region, "wind.prev_capacity"]
        next_solar = input_targets.loc[region, "solar.next_capacity"]
        next_wind = input_targets.loc[region, "wind.next_capacity"]
        zone_names = area_to_loadzone(base_grid, region)
        zone_ids = [base_grid.zone2id[n] for n in zone_names if n in grid_zones]
        if prev_solar > 0:
            scale = next_solar / prev_solar
            if abs(scale - 1) > epsilon:
                for id in zone_ids:
                    _apply_zone_scale_factor_to_ct(ct, "solar", id, scale)
        if prev_wind > 0:
            scale = next_wind / prev_wind
            if abs(scale - 1) > epsilon:
                for id in zone_ids:
                    _apply_zone_scale_factor_to_ct(ct, "wind", id, scale)
    return ct


class AbstractStrategyManager:
    """
    Base class for strategy objects, contains common functions
    """

    next_sim_hours = None

    def __init__(self):
        self.targets = {}

    @staticmethod
    def set_next_sim_hours(next_sim_hours):
        """Sets the number of hours in the simulation for next capacity
        calculations.

        :param int next_sim_hours: number of hours in the simulation
        """
        AbstractStrategyManager.next_sim_hours = next_sim_hours

    def targets_from_data_frame(self, data_frame):
        """Creates target objects from data frame.

        :param (*pandas.DataFrame*) data_frame: external target information
        """
        for row in data_frame.itertuples():

            if row.solar_percentage == "None":
                solar_percentage = None
            else:
                solar_percentage = row.solar_percentage
            target = TargetManager(
                row.region_name,
                row.ce_target_fraction,
                row.ce_category,
                row.total_demand,
                row.external_ce_addl_historical_amount,
                solar_percentage,
            )
            if row.allowed_resources == "":
                allowed_resources = ["solar", "wind"]
            else:
                split_resources = row.allowed_resources.split(",")
                allowed_resources = [x.strip() for x in split_resources]
            target.set_allowed_resources(allowed_resources)
            self.add_target(target)

    def populate_targets_with_resources(self, scenario_info, start_time, end_time):
        """Adds resource objects to all targets with a strategy from a
        specified scenario.

        :param powersimdata.design.scenario_info.ScenarioInfo scenario_info:
        ScenarioInfo object to calculate scenario resource properties
        :param str start_time: starting datetime for interval of interest
        :param str end_time: ending datetime for interval of interest
        """
        t1 = pd.to_datetime(start_time)
        t2 = pd.to_datetime(end_time)
        assert t1 < t2, "start_time must be before end_time"
        sim_hours = int((pd.Timedelta(t2 - t1).days + 1) * 24)
        AbstractStrategyManager.next_sim_hours = sim_hours

        for region_name in self.targets:
            print()
            print(region_name)
            print()
            self.targets[region_name].populate_resource_info(
                scenario_info, start_time, end_time
            )

    def add_target(self, target_manager_obj):
        """Adds target to strategy object.

        :param TargetManager target_manager_obj: target object to be added.
        """
        assert isinstance(
            target_manager_obj, TargetManager
        ), "Input must be of TargetManager type"
        self.targets[target_manager_obj.region_name] = target_manager_obj

    @staticmethod
    def load_target_from_json(target_name):
        """Loads JSON file of given target.

        :param str target_name: name of target to be loaded.
        :return: (*TargetManager*) -- instance of TargetManager class
        """
        json_file = open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "demo",
                "data",
                "save_files",
                target_name + ".json",
            ),
            "r",
        )
        target_obj = jsonpickle.decode(json_file.read())
        json_file.close()
        return target_obj

    @staticmethod
    def load_target_from_pickle(target_name):
        """Loads pickle file of given target.

        :param str target_name: name of target to be loaded
        :return: (*TargetManager*) -- instance of TargetManager class
        """
        json_file = open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "demo",
                "data",
                "save_files",
                target_name + ".pkl",
            ),
            "rb",
        )
        target_obj = pickle.load(json_file)
        json_file.close()
        return target_obj

    def create_change_table(self, ref_scenario):
        """Using a reference scenario, create a change table which scales all
        plants in a base grid to capacities matching the reference grid, with
        the exception of wind and solar plants which are scaled up according to
        the clean capacity scaling logic."""
        epsilon = 1e-3
        interconnect = ref_scenario.info["interconnect"]
        base_grid = Grid([interconnect])
        grid_zones = base_grid.plant.zone_name.unique()
        ref_grid = ref_scenario.state.get_grid()
        ct = mimic_generation_capacity(base_grid, ref_grid)
        next_capacity_df = self.data_frame_of_next_capacities()
        for region in next_capacity_df.index:
            prev_solar = next_capacity_df.loc[region, "solar_prev_capacity"]
            prev_wind = next_capacity_df.loc[region, "wind_prev_capacity"]
            next_solar = next_capacity_df.loc[region, "next_solar_capacity"]
            next_wind = next_capacity_df.loc[region, "next_wind_capacity"]
            zone_names = area_to_loadzone(base_grid, region)
            zone_ids = [base_grid.zone2id[n] for n in zone_names if n in grid_zones]
            if prev_solar > 0:
                scale = next_solar / prev_solar
                if abs(scale - 1) > epsilon:
                    for id in zone_ids:
                        _apply_zone_scale_factor_to_ct(ct, "solar", id, scale)
            if prev_wind > 0:
                scale = next_wind / prev_wind
                if abs(scale - 1) > epsilon:
                    for id in zone_ids:
                        _apply_zone_scale_factor_to_ct(ct, "wind", id, scale)
        return ct


class IndependentStrategyManager(AbstractStrategyManager):
    """Calculates the next capacities using individual target shortfalls.

    """

    def __init__(self):
        AbstractStrategyManager.__init__(self)

    def set_addl_curtailment(self, additional_curtailment_table):
        """Sets additional curtailment for a region and particular resource type

        :param dict additional_curtailment_table: nested dictionary structure of
            the form: {‘Alabama’:{‘solar’: .2}, ‘Maryland’: {‘wind’: .1}}. The
            numbers are curtailment factors between 0 and 1.
        """
        for region_name, target_obj in additional_curtailment_table.items():
            for resource_name, curtailment_factor in target_obj.items():
                assert 0 <= curtailment_factor <= 1, (
                    f"***Curtailment factor for region {region_name} and "
                    f"resource {resource_name} must be between 0 and 1!***"
                )
                try:
                    self.targets[region_name].resources[
                        resource_name
                    ].set_addl_curtailment(curtailment_factor)
                    print(
                        f"Additional curtailment added {region_name}:"
                        f"{resource_name}!"
                    )
                except KeyError as e:
                    raise KeyError(
                        f"***Region {region_name} and resource "
                        f"{resource_name} not found***"
                    ) from e

    def data_frame_of_next_capacities(self):
        """Gathers next target capacity information into a data frame.

        :return: (*pandas.DataFrame*) -- data frame of next target capacities.
        """
        target_capacities = []
        for tar in self.targets:
            if self.targets[tar].ce_target_fraction == 0:
                solar_added_capacity, wind_added_capacity = (0, 0)
            else:
                solar_added_capacity, wind_added_capacity = self.targets[
                    tar
                ].calculate_added_capacity()
            target_capacity = [
                self.targets[tar].region_name,
                self.targets[tar].ce_target_fraction,
                self.targets[tar].ce_target,
                self.targets[tar].calculate_prev_ce_generation(),
                self.targets[tar].calculate_ce_shortfall(),
                solar_added_capacity,
                wind_added_capacity,
                self.targets[tar].resources["solar"].prev_capacity,
                self.targets[tar].resources["wind"].prev_capacity,
                self.targets[tar].resources["solar"].calculate_expected_cap_factor(),
                self.targets[tar].resources["wind"].calculate_expected_cap_factor(),
                self.targets[tar]
                .resources["solar"]
                .calculate_next_capacity(solar_added_capacity),
                self.targets[tar]
                .resources["wind"]
                .calculate_next_capacity(wind_added_capacity),
            ]
            target_capacities.append(target_capacity)

        target_capacities_df = pd.DataFrame(
            target_capacities,
            columns=[
                "region_name",
                "ce_target_fraction",
                "ce_target",
                "previous_ce_generation",
                "clean_energy_shortfall",
                "solar_added_capacity",
                "wind_added_capacity",
                "solar_prev_capacity",
                "wind_prev_capacity",
                "solar_expected_cap_factor",
                "wind_expected_cap_factor",
                "next_solar_capacity",
                "next_wind_capacity",
            ],
        )
        target_capacities_df = target_capacities_df.set_index("region_name")
        return target_capacities_df


class AbstractCollaborativeStrategyManager(AbstractStrategyManager):
    """Base class for Collaborative strategy objects, contains common functions.
    """

    def __init__(self):
        raise NotImplementedError("Only child classes should be instantiated")

    def set_collab_addl_curtailment(self, addl_curtailment):
        """Sets additional curtailment for Collaborative Strategy

        :param dict addl_curtailment: dictionary with '*solar*' and '*wind*'
            keys defined: {"solar": .2, "wind": .3} with values between 0 and 1.
        """
        assert set(addl_curtailment.keys()) == set(["solar", "wind"])
        assert 0 <= addl_curtailment["solar"] <= 1, (
            "solar additional " "curtailment must be " "between  0 and 1"
        )
        assert 0 <= addl_curtailment["wind"] <= 1, (
            "wind additional " "curtailment must be " "between  0 and 1"
        )
        self.addl_curtailment = addl_curtailment

    def set_solar_fraction(self, solar_fraction):
        """Sets desired solar fraction, to be used in subsequent calculations.

        :param [float/int/None] solar_fraction: solar fraction to be used in
            calculating added capacity. *None* will maintain previous ratio.
        """
        _check_solar_fraction(solar_fraction)
        self.solar_fraction = solar_fraction

    def calculate_total_prev_ce_generation(self):
        """Calculates total allowed clean energy generation

        :return: (*float*) -- total allowed clean energy generation
        """
        total_prev_ce_generation = 0
        for tar in self.targets:
            total_prev_ce_generation += self.targets[tar].calculate_prev_ce_generation()
        return total_prev_ce_generation

    def calculate_total_capacity(self, category):
        """Calculates total capacity for a resource.

        :param str category: resource category.
        :return: (*float*) -- total capacity for a resource.
        """
        total_prev_capacity = 0
        for tar in self.targets:
            total_prev_capacity += self.targets[tar].resources[category].prev_capacity
        return total_prev_capacity

    def calculate_total_generation(self, category):
        """Calculates total generation for a resource.

        :param str category: resource category.
        :return: (*float*) -- total generation for a resource.
        """
        total_prev_generation = 0
        for tar in self.targets:
            total_prev_generation += (
                self.targets[tar].resources[category].prev_generation
            )
        return total_prev_generation

    def calculate_total_capacity_factor(self, category):
        """Calculates total capacity factor for a resource.

        :param str category: resource category.
        :return: (*float*) -- total capacity factor.
        """
        # revisit where hourly factor comes from
        total_cap_factor = self.calculate_total_generation(category) / (
            self.calculate_total_capacity(category) * 8784
        )
        return total_cap_factor

    def data_frame_of_next_capacities(self):
        """Gathers next target capacity information into a data frame.

        :return: (*pandas.DataFrame*) -- data frame of next target capacities
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
                self.targets[tar].resources["solar"].prev_capacity,
                self.targets[tar].resources["wind"].prev_capacity,
                self.targets[tar].resources["solar"].prev_capacity * solar_scaling,
                self.targets[tar].resources["wind"].prev_capacity * wind_scaling,
            ]
            target_capacities.append(target_capacity)
        target_capacities_df = pd.DataFrame(
            target_capacities,
            columns=[
                "region_name",
                "ce_target_fraction",
                "ce_target",
                "previous_ce_generation",
                "clean_energy_shortfall",
                "solar_scaling",
                "wind_scaling",
                "solar_prev_capacity",
                "wind_prev_capacity",
                "next_solar_capacity",
                "next_wind_capacity",
            ],
        )
        target_capacities_df = target_capacities_df.set_index("region_name")
        return target_capacities_df


class CollaborativeStrategyManager(AbstractCollaborativeStrategyManager):
    """Calculates the next capacities using total target shortfalls.
    """

    def __init__(self):
        self.addl_curtailment = {"solar": 0, "wind": 0}
        self.solar_fraction = None
        self.targets = {}

    def calculate_total_shortfall(self):
        """Calculates total clean energy shortfall.

        :return: (*float*) -- total clean energy shortfall
        """
        total_ce_shortfall = 0
        for name, target in self.targets.items():
            total_ce_shortfall += target.calculate_ce_shortfall()
            if target.ce_target > 0:
                total_ce_shortfall -= target.calculate_ce_overgeneration()
        return total_ce_shortfall

    def calculate_participating_capacity(self, category):
        """Calculates capacity for a resource, in participating states.
        """
        participating_capacity = sum(
            [
                self.targets[tar].resources[category].prev_capacity
                for tar in self.targets
                if self.targets[tar].ce_target > 0
            ]
        )
        return participating_capacity

    def calculate_capacity_scaling(self):
        """Calculates the aggregate capacity scaling factor for solar and wind.

        :return: (*tuple*) -- solar and wind capacity scaling factors
        """
        solar_prev_capacity = self.calculate_participating_capacity("solar")
        wind_prev_capacity = self.calculate_participating_capacity("wind")
        solar_added, wind_added = self.calculate_total_added_capacity()

        solar_scaling = (solar_added / solar_prev_capacity) + 1
        wind_scaling = (wind_added / wind_prev_capacity) + 1
        return solar_scaling, wind_scaling

    def calculate_participating_capacity_factor(self, category):
        """Calculates capacity factor for a resource, in participating states.

        :param str category: resource category.
        :return: (*float*) -- total capacity factor.
        """
        participating_gen = sum(
            [
                self.targets[tar].resources[category].prev_generation
                for tar in self.targets
                if self.targets[tar].ce_target > 0
            ]
        )
        participating_cap = self.calculate_participating_capacity(category)

        total_cap_factor = participating_gen / (participating_cap * 8784)
        return total_cap_factor

    def calculate_total_expected_capacity_factor(self, category):
        """Calculates the total expected capacity for a resource.

        :param str category: resource category.
        :return: (*float*) -- total expected capacity factor
        """
        assert category in ["solar", "wind"], (
            " expected capacity factor " "only defined for solar and " "wind"
        )
        total_exp_cap_factor = self.calculate_participating_capacity_factor(
            category
        ) * (1 - self.addl_curtailment[category])
        return total_exp_cap_factor

    def calculate_total_added_capacity(self):
        """Calculates the capacity to add from total clean energy shortfall.

        :return: (*tuple*) -- solar and wind added capacities
        """
        solar_prev_capacity = self.calculate_participating_capacity("solar")
        wind_prev_capacity = self.calculate_participating_capacity("wind")
        solar_fraction = self.solar_fraction

        if solar_fraction is None:
            solar_fraction = solar_prev_capacity / (
                solar_prev_capacity + wind_prev_capacity
            )

        ce_shortfall = self.calculate_total_shortfall()
        solar_exp_cap_factor = self.calculate_total_expected_capacity_factor("solar")
        wind_exp_cap_factor = self.calculate_total_expected_capacity_factor("wind")

        if solar_fraction != 0:
            ac_scaling_factor = (1 - solar_fraction) / solar_fraction
            solar_added_capacity = ce_shortfall / (
                AbstractStrategyManager.next_sim_hours
                * (solar_exp_cap_factor + wind_exp_cap_factor * ac_scaling_factor)
            )
            wind_added_capacity = ac_scaling_factor * solar_added_capacity
        else:
            solar_added_capacity = 0
            wind_added_capacity = ce_shortfall / (
                AbstractStrategyManager.next_sim_hours * wind_exp_cap_factor
            )
        return solar_added_capacity, wind_added_capacity

    def data_frame_of_next_capacities(self):
        """Gathers next target capacity information into a data frame.

        :return: (*pandas.DataFrame*) -- data frame of next target capacities
        """
        solar_scaling, wind_scaling = self.calculate_capacity_scaling()

        target_capacities = []
        for tar in self.targets:
            # Start with previous capacities as the capacity targets
            target_solar = self.targets[tar].resources["solar"].prev_capacity
            target_wind = self.targets[tar].resources["wind"].prev_capacity
            # Then scale up only participating states' capacities
            has_real_target = self.targets[tar].ce_target > 0
            if has_real_target:
                target_solar *= solar_scaling
                target_wind *= wind_scaling
            target_capacity = [
                self.targets[tar].region_name,
                self.targets[tar].ce_target_fraction,
                self.targets[tar].ce_target,
                self.targets[tar].calculate_prev_ce_generation(),
                self.targets[tar].calculate_ce_shortfall(),
                solar_scaling if has_real_target else 1,
                wind_scaling if has_real_target else 1,
                self.targets[tar].resources["solar"].prev_capacity,
                self.targets[tar].resources["wind"].prev_capacity,
                target_solar,
                target_wind,
            ]
            target_capacities.append(target_capacity)
        target_capacities_df = pd.DataFrame(
            target_capacities,
            columns=[
                "region_name",
                "ce_target_fraction",
                "ce_target",
                "previous_ce_generation",
                "clean_energy_shortfall",
                "solar_scaling",
                "wind_scaling",
                "solar_prev_capacity",
                "wind_prev_capacity",
                "next_solar_capacity",
                "next_wind_capacity",
            ],
        )
        target_capacities_df = target_capacities_df.set_index("region_name")
        return target_capacities_df


class CollaborativeSWoGStrategyManager(AbstractCollaborativeStrategyManager):
    """Calculates the next capacities using total target shortfalls. Includes
    states without goals ('SWoG').
    """

    def __init__(self):
        self.addl_curtailment = {"solar": 0, "wind": 0}
        self.solar_fraction = None
        self.targets = {}

    def calculate_total_shortfall(self):
        """Calculates total clean energy shortfall.

        :return: (*float*) -- total clean energy shortfall
        """
        total_ce_shortfall = 0
        for name, target in self.targets.items():
            total_ce_shortfall += target.calculate_ce_shortfall()
            total_ce_shortfall -= target.calculate_ce_overgeneration()
        return total_ce_shortfall

    def calculate_capacity_scaling(self):
        """Calculates the aggregate capacity scaling factor for solar and wind.

        :return: (*tuple*) -- solar and wind capacity scaling factors
        """
        solar_prev_capacity = self.calculate_total_capacity("solar")
        wind_prev_capacity = self.calculate_total_capacity("wind")
        solar_added, wind_added = self.calculate_total_added_capacity()

        solar_scaling = (solar_added / solar_prev_capacity) + 1
        wind_scaling = (wind_added / wind_prev_capacity) + 1
        return solar_scaling, wind_scaling

    def calculate_total_added_capacity(self):
        """Calculates the capacity to add from total clean energy shortfall.

        :return: (*tuple*) -- solar and wind added capacities
        """
        solar_prev_capacity = self.calculate_total_capacity("solar")
        wind_prev_capacity = self.calculate_total_capacity("wind")
        solar_fraction = self.solar_fraction

        if solar_fraction is None:
            solar_fraction = solar_prev_capacity / (
                solar_prev_capacity + wind_prev_capacity
            )

        ce_shortfall = self.calculate_total_shortfall()
        solar_exp_cap_factor = self.calculate_total_expected_capacity_factor("solar")
        wind_exp_cap_factor = self.calculate_total_expected_capacity_factor("wind")

        if solar_fraction != 0:
            ac_scaling_factor = (1 - solar_fraction) / solar_fraction
            solar_added_capacity = ce_shortfall / (
                AbstractStrategyManager.next_sim_hours
                * (solar_exp_cap_factor + wind_exp_cap_factor * ac_scaling_factor)
            )
            wind_added_capacity = ac_scaling_factor * solar_added_capacity
        else:
            solar_added_capacity = 0
            wind_added_capacity = ce_shortfall / (
                AbstractStrategyManager.next_sim_hours * wind_exp_cap_factor
            )
        return solar_added_capacity, wind_added_capacity

    def calculate_total_expected_capacity_factor(self, category):
        """Calculates the total expected capacity for a resource.

        :param str category: resource category.
        :return: (*float*) -- total expected capacity factor
        """
        assert category in ["solar", "wind"], (
            " expected capacity factor " "only defined for solar and " "wind"
        )
        total_exp_cap_factor = self.calculate_total_capacity_factor(category) * (
            1 - self.addl_curtailment[category]
        )
        return total_exp_cap_factor


class TargetManager:
    def __init__(
        self,
        region_name,
        ce_target_fraction,
        ce_category,
        total_demand,
        external_ce_addl_historical_amount=0,
        solar_percentage=None,
    ):
        """Manages the regional data and calculations.

        :param str region_name: region region_name
        :param float ce_target_fraction: target_manager_obj fraction for clean
            energy
        :param str ce_category: type of energy target_manager_obj, i.e.
            renewable, clean energy, etc.
        :param float total_demand: total demand for region
        """
        assert type(region_name) == str, "region_name must be a string"
        assert type(ce_category) == str, "ce_category must be a string"
        assert total_demand >= 0, "total_demand must be greater than zero"
        assert 0 <= ce_target_fraction <= 1, (
            "ce_target_fraction must be " "between 0 and 1"
        )
        err_msg = "external_ce_addl_historical_amount must be non-negative"
        assert external_ce_addl_historical_amount >= 0, err_msg
        self.region_name = region_name
        self.ce_category = ce_category

        self.total_demand = total_demand
        self.ce_target_fraction = ce_target_fraction
        self.ce_target = self.total_demand * self.ce_target_fraction
        self.external_ce_addl_historical_amount = external_ce_addl_historical_amount
        _check_solar_fraction(solar_percentage)
        self.solar_percentage = solar_percentage

        self.allowed_resources = []
        self.resources = {}

    def populate_resource_info(self, scenario_info, start_time, end_time):
        """Adds resource objects to target using a specified scenario.

        :param powersimdata.design.scenario_info.ScenarioInfo scenario_info:
            ScenarioInfo object to calculate scenario resource properties.
        :param str start_time: starting datetime for interval of interest.
        :param str end_time: ending datetime for interval of interest.
        """
        allowed_resources = set(self.allowed_resources)
        available_resources = set(
            scenario_info.get_available_resource(self.region_name)
        )
        all_resources = available_resources.union(allowed_resources)

        resources = ResourceManager()
        resources.pull_region_resource_info(
            self.region_name, scenario_info, all_resources, start_time, end_time
        )
        self.add_resource_manager(resources)

    def calculate_added_capacity(self):
        """Calculates added capacity, maintains solar wind ratio by default.

        :return: (*tuple*) -- solar and wind added capacity values
        """
        solar = self.resources["solar"]
        wind = self.resources["wind"]
        solar_percentage = self.solar_percentage
        if solar_percentage is None:
            solar_percentage = solar.prev_capacity / (
                solar.prev_capacity + wind.prev_capacity
            )
        ce_shortfall = self.calculate_ce_shortfall()

        if solar_percentage != 0:
            ac_scaling_factor = (1 - solar_percentage) / solar_percentage
            solar_added_capacity = ce_shortfall / (
                AbstractStrategyManager.next_sim_hours
                * (
                    solar.calculate_expected_cap_factor()
                    + wind.calculate_expected_cap_factor() * ac_scaling_factor
                )
            )
            wind_added_capacity = ac_scaling_factor * solar_added_capacity

        else:
            solar_added_capacity = 0
            wind_added_capacity = ce_shortfall / (
                AbstractStrategyManager.next_sim_hours
                * wind.calculate_expected_cap_factor()
            )

        return solar_added_capacity, wind_added_capacity

    def calculate_added_capacity_gen_constant(self):
        """Calculates added capacity, maintains solar wind ratio by default.

        :return: (*tuple*) -- solar and wind added capacity values.
        """
        solar = self.resources["solar"]
        wind = self.resources["wind"]
        solar_percentage = self.solar_percentage
        if solar_percentage is None:
            solar_percentage = solar.prev_capacity / (
                solar.prev_capacity + wind.prev_capacity
            )
        ce_shortfall = self.calculate_ce_shortfall()

        if solar_percentage != 0:
            solar_added_capacity = (ce_shortfall * solar_percentage) / (
                AbstractStrategyManager.next_sim_hours
                * solar.calculate_expected_cap_factor()
            )
            wind_added_capacity = (ce_shortfall * (1 - solar_percentage)) / (
                AbstractStrategyManager.next_sim_hours
                * wind.calculate_expected_cap_factor()
            )

        else:
            solar_added_capacity = 0
            wind_added_capacity = (
                ce_shortfall
                / AbstractStrategyManager.next_sim_hours
                / wind.calculate_expected_cap_factor()
            )

        return solar_added_capacity, wind_added_capacity

    def calculate_prev_ce_generation(self):
        """Calculates total generation from allowed resources.

        :return: (*float*) -- total generation from allowed resources
        """
        # prev_ce_generation = the sum of all prev_generation in the list
        # of allowed resources
        prev_ce_generation = sum(
            [self.resources[res].prev_generation for res in self.allowed_resources]
        )
        return prev_ce_generation

    def add_resource(self, resource):
        """Adds resource to TargetManager.

        :param Resource resource: resource to be added
        """
        assert isinstance(resource, Resource), "Input must be of Resource type"
        self.resources[resource.name] = resource

    def add_resource_manager(self, resource_manager):
        """Sets the resources property equal to a resource manager object which
        contains scenario resource information.

        :param ResourceManager resource_manager: resource manager object with
            scenario resource information
        """
        assert isinstance(
            resource_manager, ResourceManager
        ), "Input parameter must be an instance of type ResourceManager"
        self.resources = resource_manager

    def calculate_ce_shortfall(self):
        """Calculates the clean energy shortfall for target_manager_obj area,
        subtracts the external value if greater than total allowed clean energy
        generation.

        :return: (*float*) -- clean energy shortfall
        """
        prev_ce_generation = (
            self.calculate_prev_ce_generation()
            + self.external_ce_addl_historical_amount
        )
        ce_shortfall = max(0, self.ce_target - prev_ce_generation)

        return ce_shortfall

    def calculate_ce_overgeneration(self):
        """Calculates the clean energy over generation, subtracts from external
            value if greater than total allowed clean energy generation

        :return: (*float*) -- clean energy over generation
        """
        prev_ce_generation = (
            self.calculate_prev_ce_generation()
            + self.external_ce_addl_historical_amount
        )
        ce_overgeneration = max(0, prev_ce_generation - self.ce_target)
        return ce_overgeneration

    def set_allowed_resources(self, allowed_resources):
        """Sets a list of allowed resources.

        :param list allowed_resources: allowed resources

        .. todo:: input validation
        """
        self.allowed_resources = allowed_resources

    def save_target_as_json(self):
        """Saves target object as indented JSON file named by region name.

        """
        print(os.getcwd())
        json_file = open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "demo",
                "data",
                "save_files",
                self.region_name + ".json",
            ),
            "w",
        )
        obj_json = json.dumps(
            json.loads(jsonpickle.encode(self)), indent=4, sort_keys=True
        )
        json_file.write(obj_json)
        json_file.close()

    def save_target_as_pickle(self):
        """Saves target object as pickle file named by region name.

        """
        print(os.getcwd())
        json_file = open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "demo",
                "data",
                "save_files",
                self.region_name + ".pkl",
            ),
            "wb",
        )
        pickle.dump(self, json_file)
        json_file.close()

    def __str__(self):
        """Outputs indented JSON string af object properties.

        :return: (*str*) -- JSON formatted string
        """
        return json.dumps(
            json.loads(jsonpickle.encode(self, unpicklable=False)),
            indent=4,
            sort_keys=True,
        )


class ResourceManager:
    """Manages the creation of resource objects from scenario information.

    """

    def __init__(self):
        """Creates an empty dictionary to hold resource objects.

        """
        self.resources = {}

    def __getitem__(self, key):
        """Allows indexing into the resources dictionary directly from the
        object variable, i.e. res = ResourceManager; res["solar"] is the
        same as res.resources["solar"].

        :param str key: resource type as string
        :raises KeyError For attempts to use key not in the dictionary
        :return: instance of Resource class
        """
        try:
            return self.resources[key]
        except KeyError as e:
            print(e)

    def pull_region_resource_info(
        self, region_name, scenario_info, region_resources, start_time, end_time
    ):
        """Pulls resource information from scenario info object over the
        specified time range.

        :param str region_name: name of region to extract from scenario
        :param powersimdata.design.scenario_info.ScenarioInfo scenario_info:
        ScenarioInfo instance to calculate scenario resource properties
        :param set region_resources: resources to extract from scenario.
        :param str start_time: starting time for simulation.
        :param str end_time: ending time for simulation.
        """
        assert isinstance(
            scenario_info, ScenarioInfo
        ), "input parameter must be an instance of type ScenarioInfo"

        for resource_name in region_resources:
            resource_obj = Resource(resource_name, int(scenario_info.info["id"]))

            prev_capacity = scenario_info.get_capacity(resource_name, region_name)

            if prev_capacity == 0:
                prev_cap_factor = 0
                print("No existing resource " + resource_name + "!")
            else:
                prev_cap_factor = scenario_info.get_capacity_factor(
                    resource_name, region_name, start_time, end_time
                )

            prev_generation = scenario_info.get_generation(
                resource_name, region_name, start_time, end_time
            )

            try:
                prev_curtailment = scenario_info.get_curtailment(
                    resource_name, region_name, start_time, end_time
                )
            except Exception as e:
                print(e)
                prev_curtailment = 0

            try:
                no_congestion_cap_factor = scenario_info.get_no_congest_capacity_factor(
                    resource_name, region_name, start_time, end_time
                )
            except Exception as e:
                print(e)
                no_congestion_cap_factor = 0

            resource_obj.set_capacity(
                no_congestion_cap_factor, prev_capacity, prev_cap_factor
            )
            resource_obj.set_generation(prev_generation)
            resource_obj.set_curtailment(prev_curtailment)

            self.resources[resource_name] = resource_obj
            print("Added resource " + resource_name + "!")
            print()


class Resource:
    def __init__(self, name, prev_scenario_num):
        assert type(name) == str, "name must be a string"
        assert type(prev_scenario_num) == int, "prev_scenario_num must be and integer"
        self.name = name
        self.prev_scenario_num = prev_scenario_num
        self.no_congestion_cap_factor = None
        self.prev_capacity = None
        self.prev_cap_factor = None
        self.prev_generation = None
        self.prev_curtailment = None
        self.addl_curtailment = 0

    def set_capacity(
        self, no_congestion_cap_factor, prev_capacity, prev_cap_factor, tolerance=1e-3
    ):
        """Sets capacity information for resource.

        :param float no_congestion_cap_factor: capacity factor with no
            congestion.
        :param float prev_capacity: capacity from scenario run.
        :param float prev_cap_factor: capacity factor from scenario run.
        :param float tolerance: tolerance for values outside expected range.

        .. todo:: calculate directly from scenario results
        """
        if (-1 * tolerance) <= no_congestion_cap_factor <= 0:
            no_congestion_cap_factor = 0
        if 1 <= no_congestion_cap_factor <= (1 + tolerance):
            no_congestion_cap_factor = 1
        if (-1 * tolerance) <= prev_cap_factor <= 0:
            prev_cap_factor = 0
        if 1 <= prev_cap_factor <= (1 + tolerance):
            prev_cap_factor = 1

        assert (
            0 <= no_congestion_cap_factor <= 1
        ), "no_congestion_cap_factor must be between 0 and 1"
        assert 0 <= prev_cap_factor <= 1, "prev_cap_factor must be between 0 and 1"
        assert prev_capacity >= 0, "prev_capacity must be greater than zero"

        self.no_congestion_cap_factor = no_congestion_cap_factor
        self.prev_capacity = prev_capacity
        self.prev_cap_factor = prev_cap_factor

    def set_generation(self, prev_generation, tolerance=1e-3):
        """Sets generation from scenario run.

        :param float prev_generation: generation from scenario run.
        :param float tolerance: tolerance for ignored negative values.

        .. todo:: calculate directly from scenario results
        """
        if (-1 * tolerance) <= prev_generation < 0:
            prev_generation = 0
        assert (
            prev_generation >= 0
        ), f"prev_generation must be greater than zero. Got {prev_generation}"
        self.prev_generation = prev_generation

    def set_curtailment(self, prev_curtailment, tolerance=1e-3):
        """Sets curtailment from scenario run.

        :param float prev_curtailment: calculated curtailment from scenario run.
        """
        if (-1 * tolerance) <= prev_curtailment < 0:
            prev_curtailment = 0
        assert prev_curtailment >= 0, "prev_curtailment must be greater than zero"
        self.prev_curtailment = prev_curtailment

    def set_addl_curtailment(self, addl_curtailment):
        """Sets additional curtailment to include in capacity calculations.

        :param float addl_curtailment: additional curtailment
        """
        assert (
            0 <= addl_curtailment <= 1
        ), "additional_curtailment must be between 0 and 1"
        self.addl_curtailment = addl_curtailment

    def calculate_expected_cap_factor(self):
        """Calculates the capacity factor including additional curtailment.

        :return: (*float*) --capacity factor for resource
        """
        exp_cap_factor = self.prev_cap_factor * (1 - self.addl_curtailment)
        return exp_cap_factor

    def calculate_next_capacity(self, added_capacity):
        """Calculates next capacity to be used for scenario.

        :param float added_capacity: calculated added capacity
        :return: (*float*) -- next capacity to be used for scenario
        """
        next_capacity = self.prev_capacity + added_capacity
        return next_capacity

    def __str__(self):
        """Outputs indented JSON string af object properties

        :return: (*str*) --JSON formatted string
        """
        return json.dumps(
            json.loads(jsonpickle.encode(self, unpicklable=False)),
            indent=4,
            sort_keys=True,
        )
