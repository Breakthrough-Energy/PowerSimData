import pandas as pd

from powersimdata.design.investment.investment_costs import _calculate_ac_inv_costs
from powersimdata.input.grid import Grid
from powersimdata.network.model import area_to_loadzone
from powersimdata.utility.distance import haversine


def _find_branches_connected_to_bus(branch, bus_id):
    """Find all branches connected to a given bus.

    :param pandas.DataFrame branch: branch DataFrame from Grid object.
    :param int bus_id: index of bus to find neighbors of.
    :return: (*set*) -- set of bus indexes (integers).
    """
    branches_from = branch.index[branch["from_bus_id"] == bus_id].tolist()
    branches_to = branch.index[branch["to_bus_id"] == bus_id].tolist()

    branches_connected = set(branches_from) | set(branches_to)

    return branches_connected


def _find_first_degree_branches(branch, branch_id):
    """Find all branches connected to a given branch.

    :param pandas.DataFrame branch: branch DataFrame from Grid object.
    :param int branch_id: index of branches to find neighbors of.
    :return: (*set*) -- set of branch indexes (integers).
    """
    from_bus = branch.loc[branch_id, "from_bus_id"]
    to_bus = branch.loc[branch_id, "to_bus_id"]
    endpoints = (from_bus, to_bus)
    to_endpoints = branch.index[branch["to_bus_id"].isin(endpoints)]
    from_endpoints = branch.index[branch["from_bus_id"].isin(endpoints)]
    first_degree_branch_idxs = set(to_endpoints) | set(from_endpoints)

    return first_degree_branch_idxs


def _find_stub_degree(branch, bus_id):
    """Find degree of stubbiness, and stub branches.

    :param pandas.DataFrame branch: branch DataFrame from Grid object.
    :param int bus_id: index of bus to find subbiness of.
    :return: (*tuple*) -- tuple containing:
        stub_degree (*int*) -- How stubby (non-negative integer).
        connected_branches (*set*) -- set of branch indexes (integers).
    """
    connected_branch_idxs = _find_branches_connected_to_bus(branch, bus_id)
    if len(connected_branch_idxs) == 1:
        second_degree_branch_idxs = _find_first_degree_branches(
            branch, tuple(connected_branch_idxs)[0]
        )
        if len(second_degree_branch_idxs) == 2:
            # We could keep going recursively, but this is the max in Western.
            return 2, second_degree_branch_idxs
        else:
            return 1, connected_branch_idxs
    else:
        return 0, set()


def _find_capacity_at_bus(plant, bus_id, gentypes):
    """Find total capacity of plants with the given type(s) at the given bus.

    :param pandas.DataFrame plant: plant DataFrame from Grid object.
    :param int bus_id: index of bus to find generators at.
    :param [list/tuple/set/str] gentypes: list/tuple/set of strs, or one str,
        containing the type of generators to sum capacity for.
    :return: (*float*) -- total capacity at bus.
    """

    if isinstance(gentypes, str):
        gentypes = (gentypes,)
    gentype_plants = plant[plant["type"].isin(gentypes)]
    at_bus = gentype_plants["bus_id"] == bus_id
    gentype_plants_at_bus = gentype_plants[at_bus]
    gentype_capacity = gentype_plants_at_bus["Pmax"].sum()

    return gentype_capacity


def scale_renewable_stubs(change_table, fuzz=1, inplace=True, verbose=False):
    """Identify renewable gens behind 'stub' branches, scale up branch capacity
        (via change_table entries) to match generator capacity.

    :param powersimdata.input.change_table.ChangeTable change_table:
        change table instance.
    :param float/int fuzz: adds just a little extra capacity to avoid binding.
    :param bool inplace: if True, modify ct inplace and return None. If False,
        copy ct and return modified copy.
    :param bool verbose: if True, print info for each unscaled plant.
    :return: (*None*/*dict*) -- if inplace == True, return modified ct dict.
    """

    if inplace:
        ct = change_table.ct
    else:
        ct = change_table.ct.copy()
    ref_plant = change_table.grid.plant
    ref_branch = change_table.grid.branch
    ref_bus = change_table.grid.bus
    if "branch" not in ct:
        ct["branch"] = {}
    if "branch_id" not in ct["branch"]:
        ct["branch"]["branch_id"] = {}
    branch_id_ct = ct["branch"]["branch_id"]

    ren_types = ("hydro", "solar", "wind", "wind_offshore")
    for r in ren_types:
        ren_plants = ref_plant[ref_plant["type"] == r]
        for p in ren_plants.index:
            bus_id = ref_plant.loc[p, "bus_id"]
            stub_degree, stub_branches = _find_stub_degree(ref_branch, bus_id)
            if stub_degree > 0:
                ren_capacity = _find_capacity_at_bus(ref_plant, bus_id, r)
                if ren_capacity <= 0:
                    print("%s plant %s at bus %s has 0 Pmax!" % (r, p, bus_id))
                    continue
                # Calculate total scaling factor (zone * plant)
                gen_scale_factor = 1
                # First scale by zone_id
                zone_id = ref_bus.loc[bus_id, "zone_id"]
                try:
                    gen_scale_factor *= ct[r]["zone_id"][zone_id]
                except KeyError:
                    pass
                # Then scale by plant_id
                try:
                    gen_scale_factor *= ct[r]["plant_id"][p]
                except KeyError:
                    pass
                if verbose and gen_scale_factor == 1:
                    print(f"no scaling factor for {r}, {zone_id}, plant {p}")
                for b in stub_branches:
                    if ref_branch.loc[b, "rateA"] == 0:
                        continue
                    old_branch_cap = ref_branch.loc[b, "rateA"]
                    if old_branch_cap < ren_capacity * gen_scale_factor:
                        new_branch_cap = ren_capacity * gen_scale_factor + fuzz
                        branch_id_ct[b] = new_branch_cap / old_branch_cap

    if not inplace:
        return ct


def get_branches_by_area(grid, area_names, method="either"):
    """Given a set of area names, select branches which are in one or more of
    these areas.

    :param powersimdata.input.grid.Grid grid: Grid to query for topology.
    :param list/set/tuple area_names: an iterable of area names, used to look
        up zone names via :func:`powersimdata.network.model.area_to_loadzone`.
    :param str method: whether to include branches which span zones. Options:
        - 'internal': only select branches which are to/from the same area.
        - 'bridging': only select branches which connect area to another.
        - 'either': select branches if either end is in area. Equivalent to
        'internal' + 'bridging'.
    :raise TypeError: if area_names not a list/set/tuple, or method not a str.
    :raise ValueError: if not all elements of area_names are strings, if method
        is not one of the recognized methods.
    :return: (*set*) -- a set of branch IDs.
    """
    allowed_methods = {"internal", "bridging", "either"}
    if not isinstance(grid, Grid):
        raise TypeError("grid must be a Grid object")
    if not isinstance(area_names, (list, set, tuple)):
        raise TypeError("area_names must be list, set, or tuple")
    if not all([isinstance(a, str) for a in area_names]):
        raise ValueError("each value in area_names must be a str")
    if not isinstance(method, str):
        raise TypeError("method must be a str")
    if method not in allowed_methods:
        raise ValueError("valid methods are: " + " | ".join(allowed_methods))

    branch = grid.branch
    selected_branches = set()
    for a in area_names:
        load_zone_names = area_to_loadzone(grid.grid_model, a)
        to_bus_in_area = branch.to_zone_name.isin(load_zone_names)
        from_bus_in_area = branch.from_zone_name.isin(load_zone_names)
        if method in ("internal", "either"):
            internal_branches = branch[to_bus_in_area & from_bus_in_area].index
            selected_branches |= set(internal_branches)
        if method in ("bridging", "either"):
            bridging_branches = branch[to_bus_in_area ^ from_bus_in_area].index
            selected_branches |= set(bridging_branches)

    return selected_branches


def scale_congested_mesh_branches(
    change_table,
    ref_scenario,
    upgrade_n=100,
    allow_list=None,
    deny_list=None,
    congestion_metric="quantile",
    cost_metric="branches",
    quantile=None,
    increment=1,
):
    """Use a reference scenario to detect congested mesh branches (based on values of
    the shadow price of congestion), and increase the capacity of a subset of them.
    Branches are ranked by a ratio of (congestion metric) / (cost metric), and the top N
    branches are selected for upgrading, where N is specified by ``upgraade_n``, with
    each upgraded by their base capacity multiplied by ``increment``.

    :param powersimdata.input.change_table.ChangeTable change_table: the
        change table instance we are operating on.
    :param powersimdata.scenario.scenario.Scenario ref_scenario: the reference
        scenario to be used in bootstrapping the branch scaling factors.
    :param int upgrade_n: the number of branches to upgrade.
    :param list/set/tuple/None allow_list: only select from these branch IDs.
    :param list/set/tuple/None deny_list: never select any of these branch IDs.
    :param str congestion_metric: numerator method: 'quantile' or 'mean'.
    :param str cost_metric: denominator method: 'branches', 'cost', 'MW', or
        'MWmiles'.
    :param float quantile: if ``congestion_metric`` == 'quantile', this is the quantile
        to use to judge branch congestion (otherwise it is unused). If None, a default
        value of 0.95 is used, i.e. we evaluate the shadow price for the worst 5% of
        hours.
    :param float/int increment: branch increment, relative to original
        capacity.
    :return: (*None*) -- the change_table is modified in-place.
    """
    # To do: better type checking of inputs.
    # We need a Scenario object that's in Analyze state to get congu/congl,
    # but we can't import Scenario to check against, because circular imports.
    branches_to_upgrade = _identify_mesh_branch_upgrades(
        ref_scenario,
        upgrade_n=upgrade_n,
        congestion_metric=congestion_metric,
        cost_metric=cost_metric,
        allow_list=allow_list,
        deny_list=deny_list,
        quantile=quantile,
    )
    _increment_branch_scaling(
        change_table, branches_to_upgrade, ref_scenario, value=increment
    )


def _identify_mesh_branch_upgrades(
    ref_scenario,
    upgrade_n=100,
    allow_list=None,
    deny_list=None,
    congestion_metric="quantile",
    cost_metric="branches",
    quantile=None,
):
    """Identify the N most congested branches in a previous scenario, based on
    the quantile value of congestion duals, where N is specified by ``upgrade_n``. A
    quantile value of 0.95 obtains the branches with highest dual in top 5% of hours.

    :param powersimdata.scenario.scenario.Scenario ref_scenario: the reference
        scenario to be used to determine the most congested branches.
    :param int upgrade_n: the number of branches to upgrade.
    :param list/set/tuple/None allow_list: only select from these branch IDs.
    :param list/set/tuple/None deny_list: never select any of these branch IDs.
    :param str congestion_metric: numerator method: 'quantile' or 'mean'.
    :param str cost_metric: denominator method: 'branches', 'cost', 'MW', or
        'MWmiles'.
    :param float quantile: if ``congestion_metric`` == 'quantile', this is the quantile
        to use to judge branch congestion (otherwise it is unused). If None, a default
        value of 0.95 is used, i.e. we evaluate the shadow price for the worst 5% of
        hours.
    :raises ValueError: if ``congestion_metric`` or ``cost_metric`` is not recognized,
        ``congestion_metric`` == 'mean' but a ``quantile`` is specified, or
        ``congestion_metric`` == 'quantile' but there are not enough branches which are
        congested at the desired frequency based on the ``quantile`` specified.
    :return: (*set*) -- A set of ints representing branch indices.
    """

    # How big does a dual value have to be to be 'real' and not barrier cruft?
    cong_significance_cutoff = 1e-6  # $/MWh
    # If we rank by MW-miles, what 'length' do we give to zero-length branches?
    zero_length_value = 1  # miles
    # If the quantile is not provided, what should we default to?
    default_quantile = 0.95

    # Validate congestion_metric input
    allowed_congestion_metrics = ("mean", "quantile")
    if congestion_metric not in allowed_congestion_metrics:
        allowed_list = ", ".join(allowed_congestion_metrics)
        raise ValueError(f"congestion_metric must be one of: {allowed_list}")
    if congestion_metric == "mean" and quantile is not None:
        raise ValueError("quantile cannot be specified if congestion_metric is 'mean'")
    if congestion_metric == "quantile" and quantile is None:
        quantile = default_quantile

    # Validate cost_metric input
    allowed_cost_metrics = ("branches", "MW", "MWmiles", "cost")
    if cost_metric not in allowed_cost_metrics:
        allowed_list = ", ".join(allowed_cost_metrics)
        raise ValueError(f"cost_metric must be one of: {allowed_list}")

    # Get raw congestion dual values, add them
    ref_cong_abs = ref_scenario.state.get_congu() + ref_scenario.state.get_congl()
    all_branches = set(ref_cong_abs.columns.tolist())
    # Create validated composite allow list, and filter shadow price data frame
    composite_allow_list = _construct_composite_allow_list(
        all_branches, allow_list, deny_list
    )
    ref_cong_abs = ref_cong_abs.filter(items=composite_allow_list)

    if congestion_metric == "mean":
        congestion_metric_values = ref_cong_abs.mean()
    if congestion_metric == "quantile":
        congestion_metric_values = ref_cong_abs.quantile(quantile)

    # Filter out 'insignificant' values
    congestion_metric_values = congestion_metric_values.where(
        congestion_metric_values > cong_significance_cutoff
    ).dropna()
    # Filter based on composite allow list
    congested_indices = list(congestion_metric_values.index)

    # Ensure that we have enough congested branches to upgrade
    num_congested = len(congested_indices)
    if num_congested < upgrade_n:
        err_msg = "not enough congested branches: "
        err_msg += f"{upgrade_n} desired, but only {num_congested} congested."
        if congestion_metric == "quantile":
            err_msg += (
                f" The quantile used is {quantile}; increasing this value will increase"
                " the number of branches which qualify as having 'frequent-enough'"
                " congestion and can be selected for upgrades."
            )
        raise ValueError(err_msg)

    # Calculate selected cost metric for congested branches
    if cost_metric == "cost":
        # Calculate costs for an upgrade dataframe containing only composite_allow_list
        base_grid = ref_scenario.get_base_grid()
        base_grid.branch = base_grid.branch.filter(items=congested_indices, axis=0)
        upgrade_costs = _calculate_ac_inv_costs(base_grid, sum_results=False)
        # Merge the individual line/transformer data into a single Series
        merged_upgrade_costs = pd.concat([v for v in upgrade_costs.values()])
    if cost_metric in ("MW", "MWmiles"):
        ref_grid = ref_scenario.state.get_grid()
        branch_ratings = ref_grid.branch.loc[congested_indices, "rateA"]
        # Calculate 'original' branch capacities, since that's our increment
        ref_ct = ref_scenario.state.get_ct()
        try:
            branch_ct = ref_ct["branch"]["branch_id"]
        except KeyError:
            branch_ct = {}
        branch_prev_scaling = pd.Series(
            {i: (branch_ct[i] if i in branch_ct else 1) for i in congested_indices}
        )
        branch_ratings = branch_ratings / branch_prev_scaling
    # Then, apply this metric
    if cost_metric == "MW":
        branch_metric = congestion_metric_values / branch_ratings
    elif cost_metric == "MWmiles":
        branch_lengths = ref_grid.branch.loc[congested_indices].apply(
            lambda x: haversine((x.from_lat, x.from_lon), (x.to_lat, x.to_lon)), axis=1
        )
        # Replace zero-length branches by designated default, don't divide by 0
        branch_lengths = branch_lengths.replace(0, value=zero_length_value)
        branch_metric = congestion_metric_values / (branch_ratings * branch_lengths)
    elif cost_metric == "cost":
        branch_metric = congestion_metric_values / merged_upgrade_costs
    else:
        # By process of elimination, all that's left is method 'branches'
        branch_metric = congestion_metric_values

    # Sort by our metric, grab indexes for N largest values (tail), return
    ranked_branches = set(branch_metric.sort_values().tail(upgrade_n).index)
    return ranked_branches


def _construct_composite_allow_list(valid_branches, allow_list, deny_list):
    """Create a set of allowed branches by selecting from a set of all branches
    either only from the allow list, or everything but the deny list.

    :param list/set/tuple valid_branches: List of valid branches to select.
    :param list/set/tuple/None allow_list: only select from these branch IDs.
    :param list/set/tuple/None deny_list: never select any of these branch IDs.
    :raises ValueError: if both allow_list and deny_list are specified, or if
        allow_list or deny_list contain IDs not in valid_branches.
    :raises TypeError: if valid_branches, allow_list, or deny_list are bad type.
    :return (*set*) -- set of allowed branch IDs.
    """
    # Validate valid_branches/allow_list/deny_list Type and combination
    iterable_types = (list, set, tuple)
    if not isinstance(valid_branches, iterable_types):
        raise TypeError("allow_list must be a list, tuple, set, or None")
    if not ((allow_list is None) or isinstance(allow_list, iterable_types)):
        raise TypeError("allow_list must be a list, tuple, set, or None")
    if not ((deny_list is None) or isinstance(deny_list, iterable_types)):
        raise TypeError("deny_list must be a list, tuple, set, or None")
    if (allow_list is not None) and (deny_list is not None):
        raise ValueError("Cannot specify both allow_list and deny_list")

    # Validate allow_list (if not None), create set of allowed branch IDs
    if allow_list is None:
        composite_allow_list = set(valid_branches)
    else:
        if set(allow_list) <= set(valid_branches):
            composite_allow_list = set(allow_list)
        else:
            raise ValueError("allow_list contains branch IDs not in results")
    # Validate deny_list (if not None), subtract from set of allowed branch IDs
    if deny_list is not None:
        if set(deny_list) <= set(valid_branches):
            composite_allow_list -= set(deny_list)
        else:
            raise ValueError("deny_list contains branch IDs not in results")

    return composite_allow_list


def _increment_branch_scaling(change_table, branch_ids, ref_scenario, value=1):
    """Modify the ct dict of a ChangeTable object based on branch scaling from
    both a reference scenario and a set of branches to increment by a value.

    :param powersimdata.input.change_table.ChangeTable change_table: the
        change table instance we are operating on.
    :param [list/set/tuple] branch_ids: an iterable of branch indices.
    :param powersimdata.scenario.scenario.Scenario ref_scenario: the reference
        scenario to copy branch scaling from.
    :param [int/float] value: branch increment, relative to original capacity.
    :return: (*None*) -- the change_table is modified in-place.
    """
    # Ensure that ct has proper keys
    ct = change_table.ct
    if "branch" not in ct:
        ct["branch"] = {}
    if "branch_id" not in ct["branch"]:
        ct["branch"]["branch_id"] = {}
    branch_scaling = ct["branch"]["branch_id"]

    # Get previous scenario's branch scaling
    ref_ct = ref_scenario.state.get_ct()
    try:
        ref_branch_scaling = ref_ct["branch"]["branch_id"].copy()
    except KeyError:
        ref_branch_scaling = {}

    # Determine the final ref branch scaling after incrementing
    for branch in branch_ids:
        if branch in ref_branch_scaling:
            ref_branch_scaling[branch] += value
        else:
            ref_branch_scaling[branch] = 1 + value

    # Then merge the ref branch scaling in, unless original scaling is greater
    for branch in ref_branch_scaling:
        if branch in branch_scaling:
            new_scale = max(branch_scaling[branch], ref_branch_scaling[branch])
            branch_scaling[branch] = new_scale
        else:
            branch_scaling[branch] = ref_branch_scaling[branch]
