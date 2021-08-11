import numpy as np
import pandas as pd

from powersimdata.design.mimic_grid import mimic_generation_capacity
from powersimdata.network.model import area_to_loadzone
from powersimdata.scenario.scenario import Scenario


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


def load_targets_from_csv(filename, drop_ignored=True):
    """Interprets a CSV file as a set of targets, ensuring that required columns are present,
    and filling in default values for optional columns.

    :param str filename: filepath to targets csv.
    :param bool drop_ignored: if True, drop all ignored columns from output.
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
        "area_type": np.nan,
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
    if drop_ignored:
        raw_targets.drop(ignored_columns, axis=1, inplace=True)

    for column in optional_column_defaults.keys():
        # Fill optional columns that are missing entirely
        if column not in raw_columns:
            raw_targets[column] = np.nan
    # Fill any empty cells within optional columns
    raw_targets.fillna(value=optional_column_defaults, inplace=True)

    return raw_targets


def _make_zonename2target(grid, targets):
    """Creates a dictionary of {zone_name: target_name} pairs.

    :param powersimdata.input.grid.Grid grid: Grid instance defining the set of zones.
    :param pandas.DataFrame targets: a dataframe used to look up constituent zones.
    :return: (*dict*) -- a dictionary of {zone_name: target_name} pairs.
    :raises ValueError: if a zone is not present in any target areas, or
        if a zone is present in more than one target area.
    """
    grid_model = grid.grid_model
    target_zones = {
        target_name: area_to_loadzone(grid_model, target_name)
        if pd.isnull(targets.loc[target_name, "area_type"])
        else area_to_loadzone(
            grid_model, target_name, targets.loc[target_name, "area_type"]
        )
        for target_name in targets.index.tolist()
    }
    # Check for any collisions
    zone_sets = target_zones.values()
    if len(set.union(*zone_sets)) != sum([len(t) for t in zone_sets]):
        zone_sets_list = [zone for _set in zone_sets for zone in _set]
        duplicates = {zone for zone in zone_sets_list if zone_sets_list.count(zone) > 1}
        error_areas = {
            zone: {area for area, zone_set in target_zones.items() if zone in zone_set}
            for zone in duplicates
        }
        error_msgs = [f"{k} within: {', '.join(v)}" for k, v in error_areas.items()]
        raise ValueError(f"Zone(s) within multiple area! {'; '.join(error_msgs)}")
    zonename2target = {}
    for target_name, zone_set in target_zones.items():
        # Filter out parts of states not in the interconnect(s) in this Grid
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
    if not isinstance(scenario, Scenario):
        raise TypeError("next_scenario must be a Scenario object")
    if scenario.state.name == "create":
        start_ts = pd.Timestamp(scenario.state.builder.start_date)
        end_ts = pd.Timestamp(scenario.state.builder.end_date)
    else:
        start_ts = pd.Timestamp(scenario.info["start_date"])
        end_ts = pd.Timestamp(scenario.info["end_date"])
    num_hours = (end_ts - start_ts) / pd.Timedelta(hours=1) + 1
    return num_hours


def add_resource_data_to_targets(input_targets, scenario, calculate_curtailment=False):
    """Add resource data to targets. This data includes: previous capacity,
    previous generation, previous capacity factor (with and without curtailment),
    and previous curtailment.

    :param pandas.DataFrame input_targets: table includeing target names, used to
        summarize resource data.
    :param powersimdata.scenario.scenario.Scenario scenario: A Scenario instance.
    :return: (*pandas.DataFrame*) -- DataFrame of targets including resource data.
    """
    targets = input_targets.copy()
    grid = scenario.state.get_grid()
    plant = grid.plant
    curtailment_types = ["hydro", "solar", "wind"]
    scenario_length = _get_scenario_length(scenario)

    # Map each zone in the grid to a target
    zonename2target = _make_zonename2target(grid, targets)
    plant["target_area"] = [zonename2target[z] for z in plant["zone_name"]]

    # Summarize important values by target area & type
    groupby_cols = [plant.target_area, plant.type]
    # Capacity
    capacity_groupby = plant.Pmax.groupby(groupby_cols)
    capacity_by_target_type = capacity_groupby.sum().unstack(fill_value=0)
    # Generated energy
    pg_groupby = scenario.state.get_pg().sum().groupby(groupby_cols)
    summed_generation = pg_groupby.sum().unstack(fill_value=0)
    # Calculate capacity factors
    possible_energy = scenario_length * capacity_by_target_type[curtailment_types]
    capacity_factor = summed_generation[curtailment_types] / possible_energy
    if calculate_curtailment:
        # Calculate: curtailment, no_curtailment_cap_factor
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
        wind_potential_by_target = onshore_wind_plant_sum.groupby(
            wind_plant_targets
        ).sum()
        potentials_series = [
            hydro_potential_by_target,
            solar_potential_by_target,
            wind_potential_by_target,
        ]
        potential = pd.concat(potentials_series, axis=1)
        curtailment = (
            potential - summed_generation[curtailment_types]
        ) / possible_energy
        no_curtailment_cap_factor = potential / possible_energy
    # Now add these calculations to the DataFrame
    total_capacity = capacity_by_target_type.sum()
    nonzero_capacity_resources = total_capacity[total_capacity > 0].index.tolist()
    for r in nonzero_capacity_resources:
        targets[f"{r}.prev_capacity"] = capacity_by_target_type[r]
        targets[f"{r}.prev_generation"] = summed_generation[r]
        if r in curtailment_types:
            targets[f"{r}.prev_cap_factor"] = capacity_factor[r]
            targets[f"{r}.addl_curtailment"] = 0
            if calculate_curtailment:
                targets[f"{r}.no_curtailment_cap_factor"] = no_curtailment_cap_factor[r]
                targets[f"{r}.curtailment"] = curtailment[r]

    return targets


def add_demand_to_targets(input_targets, scenario):
    """Add demand data to targets.

    :param pandas.DataFrame input_targets: table including target names, used to
        summarize demand.
    :param powersimdata.scenario.scenario.Scenario scenario: A Scenario instance.
    :return: (*pandas.DataFrame*) -- DataFrame of targets including demand data.
    """
    grid = scenario.state.get_grid()
    targets = input_targets.copy()

    zonename2target = _make_zonename2target(grid, targets)
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


def calculate_overall_shortfall(targets, method, normalized=False):
    """Calculates overall shortfall.

    :param pandas.DataFrame targets: table of targets.
    :param str method: shortfall calculation method ("independent" or "collaborative").
    :param bool normalized: whether to normalize by total demand.
    :return: (*float*) -- overall shortfall, either in MWh or normalized by
        total demand.
    """
    if not isinstance(targets, pd.DataFrame):
        raise TypeError("targets must be a pandas DataFrame")
    if "ce_shortfall" not in targets.columns:
        raise ValueError("targets missing shortfall, see add_shortfall_to_targets()")
    if not isinstance(normalized, bool):
        raise TypeError("normalized must be bool")
    allowed_methods = {"independent", "collaborative"}

    if method == "collaborative":
        participating_targets = targets[targets.ce_target > 0]
        summed_shortfall = participating_targets.ce_shortfall.sum()
        summed_overgeneration = participating_targets.ce_overgeneration.sum()
        overall_shortfall = summed_shortfall - summed_overgeneration
    elif method == "independent":
        overall_shortfall = targets.ce_shortfall.sum()
    else:
        raise ValueError(f"method must be one of: {allowed_methods}")

    if normalized:
        return overall_shortfall / targets.demand.sum()
    else:
        return overall_shortfall


def add_new_capacities_independent(
    input_targets, scenario_length, addl_curtailment=None
):
    """Calculates new capacities based on an Independent strategy.

    :param pandas.DataFrame input_targets: table of targets.
    :param int scenario_length: number of hours in new scenario.
    :param pandas.DataFrame/None addl_curtailment: additional expected curtailment
        by target/resource. If None, assumed zero for all targets/resources.
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

    # Parse inputs
    resources = ["solar", "wind"]
    targets = input_targets.copy()
    if addl_curtailment is None:
        addl_curtailment = pd.DataFrame(0, index=targets.index, columns=resources)
    else:
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
    for r in resources:
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
    new_resources = {"solar", "wind"}

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
    else:
        if not isinstance(addl_curtailment, dict):
            raise TypeError("addl_curtailment must be supplied as a dict")
        # Check that only proper keys are supplied
        if not set(addl_curtailment.keys()) <= new_resources:
            raise ValueError(f"addl_curtailment keys are limited to {new_resources}")
        # Check that values are numbers between 0 and 1
        if not all([isinstance(x, (int, float)) for x in addl_curtailment.values()]):
            raise ValueError("addl_curtailment values must be numeric")
        if any([(x < 0) or (x > 1) for x in addl_curtailment.values()]):
            raise ValueError("addl_curtailment must be between 0 and 1")
    expected_cf = participating_cap_factor * (1 - pd.Series(addl_curtailment))
    if solar_fraction is None:
        solar_fraction = participating_capacity["solar"] / participating_capacity.sum()
    avg_new_cf = (expected_cf["solar"] * solar_fraction) + (
        expected_cf["wind"] * (1 - solar_fraction)
    )
    overall_shortfall = calculate_overall_shortfall(input_targets, "collaborative")
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
    base_grid = ref_scenario.get_base_grid()
    grid_zones = base_grid.plant.zone_name.unique()
    ref_grid = ref_scenario.get_grid()
    ct = mimic_generation_capacity(base_grid, ref_grid)
    for region in input_targets.index:
        prev_solar = input_targets.loc[region, "solar.prev_capacity"]
        prev_wind = input_targets.loc[region, "wind.prev_capacity"]
        next_solar = input_targets.loc[region, "solar.next_capacity"]
        next_wind = input_targets.loc[region, "wind.next_capacity"]
        zone_names = area_to_loadzone(ref_scenario.info["grid_model"], region)
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


def calculate_clean_capacity_scaling(
    ref_scenario,
    method,
    targets=None,
    targets_filename=None,
    addl_curtailment=None,
    next_scenario=None,
    solar_fraction=None,
):
    """Given a reference scenario (to get 'baseline' values), a method, and a set
    of targets (either via a dataframe or a filename to load a dataframe),
    calculate capacities for a new scenario to meet the calculated shortfall.

    :param powersimdata.scenario.scenario.Scenario ref_scenario: Scenario instance
        to get baseline capacities and capacity factors from.
    :param str method: which capacity scaling method to use.
    :param pandas.DataFrame/None targets: a dataframe of targets,
        containing appropriate columns.
    :param str/None targets_filename: a filepath to a CSV file of targets,
        containing appropriate columns.
    :param dict/pandas.DataFrame/None addl_curtailment: additional expected curtailment,
        either by resource (for method == 'collaborative'),
        or by target/resource (for method == 'independent').
    :param powersimdata.scenario.scenario.Scenario/None next_scenario: a Scenario
        to plan for, using this Scenario's length and demand to determine capacity
        additions.
    :param float/None solar_fraction: the fraction of new capacity to be solar,
        for method == 'collaborative' only.
        For method == 'independent', these values are specified in the targets table.
    :return: (*pandas.DataFrame*) -- dataframe of targets including new capacities,
        plus intermediate values used in calculation.
    """
    allowed_methods = {"independent", "collaborative"}
    # Input validation
    if not isinstance(ref_scenario, Scenario):
        raise TypeError("ref_scenario must be a Scenario object")
    if ref_scenario.state.name != "analyze":
        raise ValueError("ref_scenario must be in Analyze state")
    if method not in allowed_methods:
        raise ValueError(f"method must be one of: {allowed_methods}")
    if targets is None and targets_filename is None:
        raise TypeError("One of targets or targets_filename must be given")
    if targets is not None and targets_filename is not None:
        raise TypeError("targets and targets_filename cannot both be given")
    if targets is not None and not isinstance(targets, pd.DataFrame):
        raise TypeError("targets must be passed as a pandas.DataFrame")
    if targets_filename is not None:
        targets = load_targets_from_csv(targets_filename)

    # Add extra information to targets
    targets = add_resource_data_to_targets(targets, ref_scenario)
    if next_scenario is not None:
        targets = add_demand_to_targets(targets, next_scenario)
        next_scenario_length = _get_scenario_length(next_scenario)
    else:
        targets = add_demand_to_targets(targets, ref_scenario)
        next_scenario_length = _get_scenario_length(ref_scenario)
    targets = add_shortfall_to_targets(targets)
    # Calculate new capacities
    if method == "independent":
        if addl_curtailment is not None:
            if not isinstance(addl_curtailment, (dict, pd.DataFrame)):
                raise TypeError("addl_curtailment must be dict or pandas.DataFrame")
            if isinstance(addl_curtailment, dict):
                addl_curtailment = pd.DataFrame.from_dict(addl_curtailment)
                if set(addl_curtailment.columns) <= set(targets.index):
                    addl_curtailment = addl_curtailment.transpose()
            if np.sum((addl_curtailment < 0).to_numpy()) > 0:
                raise ValueError("addl_curtailment contains negative values")
            if np.sum((addl_curtailment > 1).to_numpy()) > 0:
                raise ValueError("addl_curtailment contains values > 1")
        targets = add_new_capacities_independent(
            targets, next_scenario_length, addl_curtailment
        )
    elif method == "collaborative":
        targets = add_new_capacities_collaborative(
            targets, next_scenario_length, solar_fraction, addl_curtailment
        )
    return targets
