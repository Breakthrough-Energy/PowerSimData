import datetime
import sys

import networkx as nx
import numpy as np
import pandas as pd

# Importing the module, not anything in it, to avid a circular import
import powersimdata.input.grid as _grid
from powersimdata.network.model import ModelImmutables


def check_grid(grid):
    """Check whether an object is an internally-consistent Grid object.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :raises ValueError: if ``grid`` has any inconsistency
    """
    _check_grid_type(grid)
    error_messages = []
    # Run all checks which operate on a Grid object
    for check in [
        _check_attributes,
        _check_for_islanded_buses,
        _check_for_undescribed_buses,
        _check_bus_against_bus2sub,
        _check_ac_interconnects,
        _check_transformer_substations,
        _check_line_voltages,
        _check_plant_against_gencost,
        _check_connected_components,
        _check_for_loop_branches,
    ]:
        try:
            check(grid, error_messages)
        except Exception:
            error_messages.append(
                f"Exception during {check.__name__}: {sys.exc_info()[1]!r}"
            )
    # Run checks which operate on a pandas data frame
    for gencost_key in ("before", "after"):
        try:
            _check_gencost(grid.gencost[gencost_key], error_messages)
        except Exception:
            error_messages.append(
                f"Exception during _check_gencost: {gencost_key}: "
                f"{sys.exc_info()[1]!r}"
            )
    if len(error_messages) > 0:
        collected = "\n".join(error_messages)
        raise ValueError(f"Problem(s) found with grid:\n{collected}")


def _check_attributes(grid, error_messages):
    """Check whether a Grid object has the required attributes.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        ``grid`` is missing one or more required attributes.
    """
    required = {
        "branch",
        "bus",
        "bus2sub",
        "dcline",
        "data_loc",
        "gencost",
        "grid_model",
        "interconnect",
        "model_immutables",
        "plant",
        "storage",
        "sub",
    }
    for r in required:
        if not hasattr(grid, r):
            error_messages.append(f"grid object must have attribute {r}.")


def _check_for_islanded_buses(grid, error_messages):
    """Check whether a transmission network (AC & DC) does not connect to one or more
    buses.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        branches/DC lines exist in the ``grid``, but one or more buses are islanded.
    """
    if len(grid.branch) + len(grid.dcline) > 0:
        connected_buses = set().union(
            set(grid.branch.from_bus_id),
            set(grid.branch.to_bus_id),
            set(grid.dcline.from_bus_id),
            set(grid.dcline.to_bus_id),
        )
        isolated_buses = set(grid.bus.index) - connected_buses
        if len(isolated_buses) > 0:
            error_messages.append(f"islanded buses detected: {isolated_buses}.")


def _check_for_undescribed_buses(grid, error_messages):
    """Check whether any transmission elements are connected to buses that are not
    described in the bus table.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        any transmission elements are connected to buses that are not described in the
        bus table of the ``grid``.
    """
    expected_buses = set().union(
        set(grid.branch.from_bus_id),
        set(grid.branch.to_bus_id),
        set(grid.dcline.from_bus_id),
        set(grid.dcline.to_bus_id),
    )
    undescribed_buses = expected_buses - set(grid.bus.index)
    if len(undescribed_buses) > 0:
        error_messages.append(
            "buses present in transmission network but missing from bus table: "
            f"{undescribed_buses}."
        )


def _check_bus_against_bus2sub(grid, error_messages):
    """Check whether indices of bus and bus2sub tables match.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        indices of bus and bus2sub tables of the ``grid`` don't match.
    """
    if not set(grid.bus.index) == set(grid.bus2sub.index):
        error_messages.append("indices for bus and bus2sub don't match.")


def _check_ac_interconnects(grid, error_messages):
    """Check whether any AC branches bridge across interconnections.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        any AC branches bridge across interconnections of the ``grid``.
    """
    from_interconnect = grid.branch.from_bus_id.map(grid.bus.interconnect)
    to_interconnect = grid.branch.to_bus_id.map(grid.bus.interconnect)
    if not all(from_interconnect == to_interconnect):
        non_matching_ids = grid.branch.index[from_interconnect != to_interconnect]
        error_messages.append(
            "branch(es) connected across multiple interconnections: "
            f"{non_matching_ids}."
        )


def _check_transformer_substations(grid, error_messages):
    """Check whether any transformers are are not within exactly one same substation.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        any transformers in the ``grid`` are not within exactly one same substation.
    """
    txfmr_branch_types = {"Transformer", "TransformerWinding"}
    branch = grid.branch
    transformers = branch.loc[branch.branch_device_type.isin(txfmr_branch_types)]
    from_sub = transformers.from_bus_id.map(grid.bus2sub.sub_id)
    to_sub = transformers.to_bus_id.map(grid.bus2sub.sub_id)
    if not all(from_sub == to_sub):
        non_matching_transformers = transformers.index[from_sub != to_sub]
        error_messages.append(
            "transformer(s) connected across multiple substations: "
            f"{non_matching_transformers}."
        )


def _check_line_voltages(grid, error_messages):
    """Check whether any lines connect across different voltage levels.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        any lines in the ``grid`` connect across different voltage levels.
    """
    lines = grid.branch.query("branch_device_type == 'Line'")
    from_kV = lines.from_bus_id.map(grid.bus.baseKV)  # noqa: N806
    to_kV = lines.to_bus_id.map(grid.bus.baseKV)  # noqa: N806
    if not all(from_kV == to_kV):
        non_matching_lines = lines.index[from_kV != to_kV]
        error_messages.append(
            f"line(s) connected across multiple voltages: {non_matching_lines}."
        )


def _check_plant_against_gencost(grid, error_messages):
    """Check whether indices of plant and gencost tables match.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        indices of plant and gencost tables of the ``grid`` don't match.
    """
    if not (
        set(grid.plant.index)
        == set(grid.gencost["before"].index)
        == set(grid.gencost["after"].index)
    ):
        error_messages.append("indices for plant and gencost don't match.")


def _check_connected_components(grid, error_messages):
    """Check whether connected components and listed interconnects of a grid match.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        connected components and listed interconnects of a ``grid`` don't match.
    """
    g = nx.from_pandas_edgelist(grid.branch, "from_bus_id", "to_bus_id")
    num_connected_components = len([c for c in nx.connected_components(g)])
    if len(grid.interconnect) == 1:
        # Check for e.g. ['USA'] interconnect, which is really three interconnects
        interconnect_aliases = grid.model_immutables.zones["interconnect_combinations"]
        if grid.interconnect[0] in interconnect_aliases:
            num_interconnects = len(interconnect_aliases[grid.interconnect[0]])
        else:
            num_interconnects = 1
    else:
        num_interconnects = len(grid.interconnect)
    if num_interconnects != num_connected_components:
        error_messages.append(
            f"This grid contains {num_connected_components} connected components, "
            f"but is specified as having {num_interconnects} interconnects: "
            f"{grid.interconnect}."
        )


def _check_for_loop_branches(grid, error_messages):
    """Check whether any branches in a grid have the same start and end bus.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        there are any branches with the same start and end bus.
    """
    if not all(grid.branch.from_bus_id != grid.branch.to_bus_id):
        loop_lines = grid.branch.query("from_bus_id == to_bus_id").index  # noqa: F841
        error_messages.append(f"This grid contains loop lines: {list(loop_lines)}")


def _check_grid_models_match(grid1, grid2):
    """Check whether an object is an internally-consistent Grid object.

    :param powersimdata.input.grid.Grid grid1: first Grid instance.
    :param powersimdata.input.grid.Grid grid2: second Grid instance.
    :raises ValueError: if the grid models don't match.
    """
    _check_grid_type(grid1)
    _check_grid_type(grid2)
    if not grid1.grid_model == grid2.grid_model:
        raise ValueError(
            f"Grid models don't match: {grid1.grid_model}, {grid2.grid_model}"
        )


def _check_data_frame(df, label):
    """Ensure that input is a pandas data frame.

    :param pandas.DataFrame df: a data frame.
    :param str label: name of data frame (used for error messages).
    :raises TypeError: if df is not a data frame or label is not a str.
    :raises ValueError: if data frame is empty.
    """
    if not isinstance(label, str):
        raise TypeError("label must be a str")
    if not isinstance(df, pd.DataFrame):
        raise TypeError(label + " must be a pandas.DataFrame object")
    if not df.shape[0] > 0:
        raise ValueError(label + " must have at least one row")
    if not df.shape[1] > 0:
        raise ValueError(label + " must have at least one column")


def _check_time_series(ts, label):
    """Check that a time series is specified properly.

    :param pandas.DataFrame/pandas.Series ts: time series to check.
    :param str label: name of time series (used for error messages).
    :raises TypeError: if ts is not a data frame/time series or label is not a str.
    :raises ValueError: if indices are not timestamps.
    """
    if not isinstance(label, str):
        raise TypeError("label must be a str")
    if not isinstance(ts, (pd.DataFrame, pd.Series)):
        raise TypeError(label + " must be a pandas.DataFrame or pandas.Series object")
    if not ts.shape[0] > 0:
        raise ValueError(label + " must have at least one row")
    if not isinstance(ts.index, pd.DatetimeIndex):
        raise ValueError(label + " must be a time series")


def _check_grid_type(grid):
    """Ensure that ``grid`` is a Grid object.

    :param powersimdata.input.grid.Grid grid: a Grid instance.
    :raises TypeError: if input is not a Grid instance.
    """
    if not isinstance(grid, _grid.Grid):
        raise TypeError(f"grid must be a {_grid.Grid} object")


def _check_areas_and_format(areas, grid_model="usa_tamu"):
    """Ensure that areas are valid. Duplicates are removed and state abbreviations are
    converted to their actual name.

    :param str/list/tuple/set areas: areas(s) to check. Could be load zone name(s),
        state name(s)/abbreviation(s) or interconnect(s).
    :param str grid_model: grid model.
    :raises TypeError: if areas is not a list/tuple/set of str.
    :raises ValueError: if areas is empty or not valid.
    :return: (*set*) -- areas as a set. State abbreviations are converted to state
        names.
    """
    mi = ModelImmutables(grid_model)
    if isinstance(areas, str):
        areas = {areas}
    elif isinstance(areas, (list, set, tuple)):
        if not all([isinstance(z, str) for z in areas]):
            raise TypeError("all areas must be str")
        areas = set(areas)
    else:
        raise TypeError("areas must be a str or a list/tuple/set of str")
    if len(areas) == 0:
        raise ValueError("areas must be non-empty")
    all_areas = (
        mi.zones["loadzone"]
        | mi.zones["abv"]
        | mi.zones["state"]
        | mi.zones["interconnect"]
    )
    if not areas <= all_areas:
        diff = areas - all_areas
        raise ValueError("invalid area(s): %s" % " | ".join(diff))

    abv_in_areas = [z for z in areas if z in mi.zones["abv"]]
    for a in abv_in_areas:
        areas.remove(a)
        areas.add(mi.zones["abv2state"][a])

    return areas


def _check_resources_and_format(resources, grid_model="usa_tamu"):
    """Ensure that resources are valid and convert variable to a set.

    :param str/list/tuple/set resources: resource(s) to check.
    :param str grid_model: grid model.
    :raises TypeError: if resources is not a list/tuple/set of str.
    :raises ValueError: if resources is empty or not valid.
    :return: (*set*) -- resources as a set.
    """
    mi = ModelImmutables(grid_model)
    if isinstance(resources, str):
        resources = {resources}
    elif isinstance(resources, (list, set, tuple)):
        if not all([isinstance(r, str) for r in resources]):
            raise TypeError("all resources must be str")
        resources = set(resources)
    else:
        raise TypeError("resources must be a str or a list/tuple/set of str")
    if len(resources) == 0:
        raise ValueError("resources must be non-empty")
    if not resources <= mi.plants["all_resources"]:
        diff = resources - mi.plants["all_resources"]
        raise ValueError("invalid resource(s): %s" % " | ".join(diff))
    return resources


def _check_resources_are_renewable_and_format(resources, grid_model="usa_tamu"):
    """Ensure that resources are valid renewable resources and convert variable to
    a set.

    :param str/list/tuple/set resources: resource(s) to analyze.
    :param str grid_model: grid model.
    :raises ValueError: if resources are not renewables.
    return: (*set*) -- resources as a set
    """
    mi = ModelImmutables(grid_model)
    resources = _check_resources_and_format(resources, grid_model=grid_model)
    if not resources <= mi.plants["renewable_resources"]:
        diff = resources - mi.plants["all_resources"]
        raise ValueError("invalid renewable resource(s): %s" % " | ".join(diff))
    return resources


def _check_areas_are_in_grid_and_format(areas, grid):
    """Ensure that list of areas are in grid.

    :param dict areas: keys are area types: '*loadzone*', '*state*' or '*interconnect*'.
        Values are str/list/tuple/set of areas.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*dict*) -- modified areas dictionary. Keys are area types ('*loadzone*',
        '*state*' or '*interconnect*'). State abbreviations, if present, are converted
        to state names. Values are areas as a set.
    :raises TypeError: if areas is not a dict or its keys are not str.
    :raises ValueError: if area type is invalid, an area in not in grid or an
        invalid loadzone/state/interconnect is passed.
    """
    _check_grid_type(grid)
    if not isinstance(areas, dict):
        raise TypeError("areas must be a dict")

    mi = grid.model_immutables
    areas_formatted = {}
    for a in areas.keys():
        if a in ["loadzone", "state", "interconnect"]:
            areas_formatted[a] = set()

    all_loadzones = set()
    for k, v in areas.items():
        if not isinstance(k, str):
            raise TypeError("area type must be a str")
        elif k == "interconnect":
            interconnects = _check_areas_and_format(v)
            for i in interconnects:
                try:
                    all_loadzones.update(mi.zones["interconnect2loadzone"][i])
                except KeyError:
                    raise ValueError("invalid interconnect: %s" % i)
            areas_formatted["interconnect"].update(interconnects)
        elif k == "state":
            states = _check_areas_and_format(v)
            for s in states:
                try:
                    all_loadzones.update(mi.zones["state2loadzone"][s])
                except KeyError:
                    raise ValueError("invalid state: %s" % s)
            areas_formatted["state"].update(states)
        elif k == "loadzone":
            loadzones = _check_areas_and_format(v)
            for l in loadzones:
                if l not in mi.zones["loadzone"]:
                    raise ValueError("invalid load zone: %s" % l)
            all_loadzones.update(loadzones)
            areas_formatted["loadzone"].update(loadzones)
        else:
            raise ValueError("invalid area type")

    valid_loadzones = set(grid.plant["zone_name"].unique())
    if not all_loadzones <= valid_loadzones:
        diff = all_loadzones - valid_loadzones
        raise ValueError("%s not in in grid" % " | ".join(diff))

    return areas_formatted


def _check_resources_are_in_grid_and_format(resources, grid):
    """Ensure that resource(s) is represented in at least one generator in the grid
    used for the scenario.

    :param str/list/tuple/set resources: resource(s) to analyze.
    :param powersimdata.input.grid.Grid grid: a Grid instance.
    :return: (*set*) -- resources as a set.
    :raises ValueError: if resources is not used in scenario.
    """
    _check_grid_type(grid)
    resources = _check_resources_and_format(resources)
    valid_resources = set(grid.plant["type"].unique())
    if not resources <= valid_resources:
        diff = resources - valid_resources
        raise ValueError("%s not in in grid" % " | ".join(diff))
    return resources


def _check_plants_are_in_grid(plant_id, grid):
    """Ensure that list of plant id are in grid.

    :param list/tuple/set plant_id: list of plant id.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :raises TypeError: if plant_id is not a list of int or str.
    :raises ValueError: if plant id is not in network.
    """
    _check_grid_type(grid)
    if not (
        isinstance(plant_id, (list, tuple, set))
        and all([isinstance(p, (int, str)) for p in plant_id])
    ):
        raise TypeError("plant_id must be a a list/tuple/set of int or str")
    if not set([str(p) for p in plant_id]) <= set([str(i) for i in grid.plant.index]):
        raise ValueError("plant_id must be subset of plant index")


def _check_number_hours_to_analyze(scenario, hours):
    """Ensure that number of hours is greater than simulation length.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int hours: number of hours to analyze.
    :raises TypeError: if hours is not int.
    :raises ValueError: if hours is negative or greater than simulation length
    """
    start_date = pd.Timestamp(scenario.info["start_date"])
    end_date = pd.Timestamp(scenario.info["end_date"])
    if not isinstance(hours, int):
        raise TypeError("hours must be an int")
    if hours < 1:
        raise ValueError("hours must be positive")
    if hours > (end_date - start_date).total_seconds() / 3600 + 1:
        raise ValueError("hours must not be greater than simulation length")


def _check_date(date):
    """Check date is valid.

    :param pandas.Timestamp/numpy.datetime64/datetime.datetime date: timestamp.
    :raises TypeError: if date is improperly formatted.
    """
    if not isinstance(date, (pd.Timestamp, np.datetime64, datetime.datetime)):
        raise TypeError(
            "date must be a pandas.Timestamp, a numpy.datetime64 or a datetime.datetime object"
        )


def _check_date_range_in_scenario(scenario, start, end):
    """Check if start time and end time define a valid time range of the given scenario.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime start: start date.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime end: end date.
    :raises ValueError: if the date range is invalid.
    """
    _check_date(start)
    _check_date(end)
    scenario_start = pd.Timestamp(scenario.info["start_date"])
    scenario_end = pd.Timestamp(scenario.info["end_date"])

    if not scenario_start <= start <= end <= scenario_end:
        raise ValueError("Must have scenario_start <= start <= end <= scenario_end")


def _check_date_range_in_time_series(ts, start, end):
    """Check if start time and end time define a valid time range of the time series.

    :param pandas.DataFrame/pandas.Series ts: a time series with timestamp as indices.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime start: start date.
    :param pandas.Timestamp/numpy.datetime64/datetime.datetime end: end date.
    :raises ValueError: if the date range is invalid.
    """
    _check_time_series(ts, "time series")
    _check_date(start)
    _check_date(end)

    if not ts.index[0] <= start <= end <= ts.index[-1]:
        raise ValueError(
            "Must have time_series_start <= start <= end <= time_series_end"
        )


def _check_epsilon(epsilon):
    """Ensure epsilon is valid.

    :param float/int epsilon: precision for binding constraints.
    :raises TypeError: if epsilon is not a float or an int.
    :raises ValueError: if epsilon is negative.
    """
    if not isinstance(epsilon, (float, int)):
        raise TypeError("epsilon must be numeric")
    if epsilon < 0:
        raise ValueError("epsilon must be non-negative")


def _check_gencost(gencost, error_messages=None):
    """Check that gencost is valid.

    :param pandas.DataFrame gencost: cost curve polynomials.
    :param list error_messages: list to append error messages to. If `error_messages``
        is None and an error is encountered, an Exception will be raised instead.
    :raises TypeError: if ``error_messages`` is None and: gencost is not a data frame,
        or polynomial degree is not an int.
    :raises ValueError: if data frame has no rows, does not have the required columns,
        curves are not polynomials and have not the appropriate coefficients.
    """

    try:
        # check for nonempty dataframe
        if isinstance(gencost, pd.DataFrame):
            _check_data_frame(gencost, "gencost")
        else:
            print(gencost)
            raise TypeError("gencost must be a pandas.DataFrame object")

        # check for proper columns
        required_columns = ("type", "n")
        for r in required_columns:
            if r not in gencost.columns:
                raise ValueError("gencost must have column " + r)

        # check that gencosts are all specified as type 2 (polynomial)
        cost_type = gencost["type"]
        if not cost_type.where(cost_type == 2).equals(cost_type):
            raise ValueError("each gencost must be type 2 (polynomial)")

        # check that all gencosts are specified as same order polynomial
        if not (gencost["n"].nunique() == 1):
            raise ValueError("all polynomials must be of same order")

        # check that this order is an integer > 0
        n = gencost["n"].iloc[0]
        if not isinstance(n, (int, np.integer)):
            raise TypeError("polynomial degree must be specified as an int")
        if n < 1:
            raise ValueError("polynomial must be at least of order 1 (constant)")

        # check that the right columns are here for this dataframe
        coef_columns = ["c" + str(i) for i in range(n)]
        for c in coef_columns:
            if c not in gencost.columns:
                raise ValueError(f"gencost of order {n} must have column {c}")
    except Exception:
        if error_messages is not None:
            error_messages.append(repr(sys.exc_info()[1]))
        else:
            raise
