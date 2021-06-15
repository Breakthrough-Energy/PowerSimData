def calculate_interzone_capacity(grid):
    """For each zone in a grid, calculate the aggreagte zone transmission
    capacity (in a transport model, ignoring power flow).

    :param powersimdata.input.grid.Grid grid: a grid instance.
    :return: (*pandas.Series*) -- index is zone IDs, values are total transmission
        capacity (MW).
    """
    # Get new branch data frame with 'from_zone' and 'to_zone' columns
    branch = grid.branch.assign(
        from_zone_id=grid.branch.from_bus_id.map(grid.bus["zone_id"]),
        to_zone_id=grid.branch.to_bus_id.map(grid.bus["zone_id"]),
    )
    # Calculate total substation capacity for matching 'from_zone' branches
    filtered_branch = branch.query("from_zone_id != to_zone_id")
    from_cap = filtered_branch.groupby("from_zone_id").sum()["rateA"]
    to_cap = filtered_branch.groupby("to_zone_id").sum()["rateA"]
    total_capacities = from_cap.combine(to_cap, lambda x, y: x + y, fill_value=0)
    return total_capacities
