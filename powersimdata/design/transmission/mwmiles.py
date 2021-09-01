from powersimdata.input.transform_grid import TransformGrid
from powersimdata.utility.distance import haversine


def calculate_mw_miles(scenario, exclude_branches=None):
    """Given a Scenario object, calculate the number of upgraded lines and
    transformers, and the total upgrade quantity (in MW and MW-miles).
    Currently only supports change tables that specify branches' id, not
    zone name. Currently lumps Transformer and TransformerWinding upgrades
    together.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param list/tuple/set/None exclude_branches: branches to exclude.
    :return: (*dict*) -- Upgrades to the branches.
    """

    original_grid = scenario.get_base_grid()
    ct = scenario.get_ct()
    upgrades = _calculate_mw_miles(original_grid, ct, exclude_branches)
    return upgrades


def _calculate_mw_miles(original_grid, ct, exclude_branches=None):
    """Given a base grid and a change table, calculate the number of upgraded
    lines and transformers, and the total upgrade quantity (in MW & MW-miles).
    This function is separate from calculate_mw_miles() for testing purposes.
    Currently only supports change_tables that specify branches, not zone_name.
    Currently lumps Transformer and TransformerWinding upgrades together.

    :param powersimdata.input.grid.Grid original_grid: grid instance.
    :param dict ct: change table instance.
    :param list/tuple/set/None exclude_branches: branches to exclude.
    :raises ValueError: if not all values in exclude_branches are in the grid.
    :raises TypeError: if exclude_branches gets the wrong type.
    :return: (*dict*) -- Upgrades to the branches.
    """

    upgrade_categories = ("mw_miles", "transformer_mw", "num_lines", "num_transformers")
    upgrades = {u: 0 for u in upgrade_categories}

    if "branch" not in ct or "branch_id" not in ct["branch"]:
        return upgrades

    if exclude_branches is None:
        exclude_branches = {}
    elif isinstance(exclude_branches, (list, set, tuple)):
        good_branch_indices = original_grid.branch.index
        if not all([e in good_branch_indices for e in exclude_branches]):
            raise ValueError("not all branches are present in grid!")
        exclude_branches = set(exclude_branches)
    else:
        raise TypeError("exclude_branches must be None, list, tuple, or set")

    base_branch_ids = set(original_grid.branch.index)
    upgraded_branch_ids = set(ct["branch"]["branch_id"].keys())
    transformed_branch = TransformGrid(original_grid, ct).get_grid().branch
    if "new_branch" in ct:
        upgraded_branch_ids |= set(transformed_branch.index) - base_branch_ids
    for b in upgraded_branch_ids:
        if b in exclude_branches:
            continue
        if b in base_branch_ids:
            # 'upgraded' capacity is (scale - 1) because a scale of 1 = an upgrade of 0
            scale = ct["branch"]["branch_id"][b]
            upgraded_capacity = transformed_branch.loc[b, "rateA"] / scale * (scale - 1)
        else:
            upgraded_capacity = transformed_branch.loc[b, "rateA"]
        device_type = transformed_branch.loc[b, "branch_device_type"]
        if device_type == "Line":
            from_coords = (
                transformed_branch.loc[b, "from_lat"],
                transformed_branch.loc[b, "from_lon"],
            )
            to_coords = (
                transformed_branch.loc[b, "to_lat"],
                transformed_branch.loc[b, "to_lon"],
            )
            addtl_mw_miles = upgraded_capacity * haversine(from_coords, to_coords)
            upgrades["mw_miles"] += addtl_mw_miles
            upgrades["num_lines"] += 1
        elif device_type == "Transformer":
            upgrades["transformer_mw"] += upgraded_capacity
            upgrades["num_transformers"] += 1
        elif device_type == "TransformerWinding":
            upgrades["transformer_mw"] += upgraded_capacity
            upgrades["num_transformers"] += 1
        else:
            raise Exception("Unknown branch type: " + str(b))

    return upgrades
