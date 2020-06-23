def _calculate_common_zone_factors(base_plant, ref_plant, plant_scaling, epsilon=1e-3):
    """Given a base plant dataframe, a reference plant dataframe, and a scaling
    vector: calculate common zone scaling factors, and produce a change-table
    with an equivalent combination of zone and plant scaling factors.

    :param pandas.DataFrame base_plant: plant dataframe for base grid.
    :param pandas.DataFrame ref_plant: plant dataframe for reference grid.
    :param pandas.Series plant_scaling: scaling factors by plant to get from
        base_plant Pmax values to ref_plant Pmax values.
    :return: (*dict*) -- dictionary of plant/zone scaling factors in a format
        matching powersimdata.input.change_table.
    """
    change_table = {}
    new_plant_scaling = plant_scaling.copy()

    # Detect if any zones have all-zero plant scaling (e.g. wind_offshore)
    grouping = new_plant_scaling.groupby([base_plant.type, base_plant.zone_id])
    total_scale = grouping.sum()
    for (fuel, zone_id) in total_scale.index:
        if total_scale.loc[(fuel, zone_id)] == 0:
            if fuel not in change_table:
                change_table[fuel] = {"zone_id": {}}
            change_table[fuel]["zone_id"][zone_id] = 0
            # Since we have zone scaling of 0, we don't need plant scaling
            matching_indices = grouping.get_group((fuel, zone_id)).index
            matching_boolean = new_plant_scaling.index.isin(matching_indices)
            new_plant_scaling = new_plant_scaling[~matching_boolean]

    # Determine approximately most common non-zero scaling factor via median
    nonzero = plant_scaling > 0
    grouping = plant_scaling[nonzero].groupby([base_plant.type, base_plant.zone_id])
    common_factors = grouping.median()
    # Divide plant scaling factors by zone scaling factors as appropriate
    for (fuel, zone_id), v in common_factors.to_dict().items():
        if fuel not in change_table:
            change_table[fuel] = {"zone_id": {}}
        if abs(v - 1) <= epsilon:
            # Zone scaling not needed if it's close enough to 1
            continue
        else:
            change_table[fuel]["zone_id"][zone_id] = v
            # Since we have meaningful zone scaling, modify plant scaling
            matching_indices = grouping.get_group((fuel, zone_id)).index
            new_plant_scaling.loc[matching_indices] /= v

    # Drop plant scaling factors that are nearly 1
    approx_1_plants = abs(new_plant_scaling - 1) <= epsilon
    new_plant_scaling = new_plant_scaling[~approx_1_plants]
    for k, v in new_plant_scaling.to_dict().items():
        plantfuel = base_plant.loc[k, "type"]
        if plantfuel not in change_table:
            change_table[plantfuel] = {}
        if "plant_id" not in change_table[plantfuel]:
            change_table[plantfuel]["plant_id"] = {}
        change_table[plantfuel]["plant_id"][k] = v

    return change_table


def mimic_generation_capacity(base_grid, ref_grid):
    """Given a base grid and a reference grid, determine zone and plant scaling
    factors such that the combination, when applied to the base grid, produces
    the reference grid.

    :param powersimdata.input.grid.Grid base_grid: the base grid (unscaled).
    :param powersimdata.input.grid.Grid ref_grid: the base grid (unscaled).
    :return: (*dict*) -- dictionary of plant/zone scaling factors in a format
        matching ct in powersimdata.input.change_table.ChangeTable.
    """
    base_plant = base_grid.plant
    ref_plant = ref_grid.plant
    plant_scaling = ref_plant.Pmax / base_plant.Pmax
    # Element-wise division will return NaN for plants not in ref_grid
    plant_scaling = plant_scaling.fillna(0)
    change_table = _calculate_common_zone_factors(base_plant, ref_plant, plant_scaling)
    return change_table
