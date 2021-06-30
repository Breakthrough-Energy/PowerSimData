def calculate_substation_capacity(grid):
    """For each substation in a grid, calculate the total substation transmission
    capacity (in a transport model, ignoring power flow).

    :param powersimdata.input.grid.Grid grid: a grid instance.
    :return: (*pandas.Series*) -- index is substation IDs, value are total transmission
        capacity (MW).
    """
    # Get new branch data frame with 'from_sub' and 'to_sub' columns
    branch = grid.branch.assign(
        from_sub_id=grid.branch.from_bus_id.map(grid.bus2sub.sub_id),
        to_sub_id=grid.branch.to_bus_id.map(grid.bus2sub.sub_id),
    )
    # Calculate total substation capacity for matching 'from_sub' branches
    filtered_branch = branch.query("from_sub_id != to_sub_id")
    from_cap = filtered_branch.groupby("from_sub_id").sum()["rateA"]
    to_cap = filtered_branch.groupby("to_sub_id").sum()["rateA"]
    total_capacities = from_cap.combine(to_cap, lambda x, y: x + y, fill_value=0)
    return total_capacities
