import pandas as pd

from powersimdata.scenario.scenario import Scenario

default_pmin_dict = {
    "coal": None,
    "dfo": 0,
    "geothermal": 0.95,
    "hydro": None,
    "ng": 0,
    "nuclear": 0.95,
    "other": 0,
    "solar": 0,
    "wind": 0,
    "wind_offshore": 0,
}
profile_methods = {
    "hydro": "get_hydro",
    "solar": "get_solar",
    "wind": "get_wind",
    "wind_offshore": "get_wind",
}


def temporal_curtailment(
    scenario, pmin_by_type=None, pmin_by_id=None, curtailable={"solar", "wind"}
):
    """Calculate the minimum share of potential renewable energy that will be curtailed
        due to supply/demand mismatch, assuming no storage is present.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param dict/pandas.Series pmin_by_type: Mapping of types to Pmin assumptions. Values
        between 0 and 1 (inclusive) are treated as shares of Pmax, and None values
        either maintain given Pmin values (for dispatchable resources) or track profiles
        (for profile resources, e.g. hydro).
    :param dict/pandas.Series pmin_by_id: Mapping of IDs to Pmin assumptions, as an
        override to the default behavior for that plant type. Values between 0 and 1
        (inclusive) are treated as shares of Pmax, and None values either maintain given
        Pmin values (for dispatchable resources) or track profiles
        (for profile resources, e.g. hydro).
    :param iterable curtailable: resource types which can be curtailed.
    :return: (*float*) -- share of curtailable resources that will be curtailed.
    :raises TypeError: if inputs do not mach specified type.
    :raises ValueError: if any entries in curtailable or keys in pmin_by_type are not
        types in the grid, any keys in pmin_by_id are not plant IDs in the Grid,
        or any values in pmin_by_type/pmin_by_id are not in the range [0, 1] or None.
    """
    if not isinstance(scenario, Scenario):
        raise TypeError("scenario must be a Scenario")
    if pmin_by_type is None:
        pmin_by_type = {}
    if pmin_by_id is None:
        pmin_by_id = {}
    check_dicts = {"pmin_by_id": pmin_by_id, "pmin_by_type": pmin_by_type}
    for name, d in check_dicts.items():
        if not isinstance(d, (dict, pd.Series)):
            raise TypeError(f"{name} must be a dict or pandas Series")
        # Access values via appropriate method whether d is a dict or a pandas Series
        values = d.values() if isinstance(d, dict) else d.values
        if not all([v is None or 0 <= v <= 1 for v in values]):
            err_msg = f"all entries in {name} must be None or in the range [0, 1]"
            raise ValueError(err_msg)
    plant = scenario.state.get_grid().plant
    valid_types = plant["type"].unique()
    if not set(pmin_by_type.keys()) <= set(valid_types):
        raise ValueError("Got invalid plant type as a key to pmin_by_type")
    if not set(pmin_by_id.keys()) <= set(plant.index):
        raise ValueError("Got invalid plant id as a key to pmin_by_id")
    try:
        if not set(curtailable) <= set(valid_types):
            raise ValueError("Got invalid plant type within curtailable")
    except TypeError:
        raise TypeError("curtailable must be an iterable")

    # Get profiles, filter out plant-level overrides, then sum
    all_profiles = pd.concat(
        [getattr(scenario.state, m)() for m in set(profile_methods.values())], axis=1
    )
    plant_id_mask = ~plant.index.isin(pmin_by_id.keys())
    base_plant_ids_by_type = plant.loc[plant_id_mask].groupby("type").groups
    valid_profile_types = set(base_plant_ids_by_type) & set(profile_methods)
    plant_ids_for_summed_profiles = set().union(
        *[set(base_plant_ids_by_type[g]) for g in valid_profile_types]
    )
    summed_profiles = (
        all_profiles[plant_ids_for_summed_profiles].groupby(plant["type"], axis=1).sum()
    )

    # Build up a series of firm generation
    summed_demand = scenario.state.get_demand().sum(axis=1)
    firm_generation = pd.Series(0, index=summed_demand.index)
    # Add plants without plant-level overrides ('base' plants)
    pmin_dict = {**default_pmin_dict, **pmin_by_type}
    # Don't iterate over plant types not present in this grid
    pmin_dict = {k: pmin_dict[k] for k in base_plant_ids_by_type}
    for resource, pmin in pmin_dict.items():
        if (resource in curtailable) or (pmin == 0):
            continue
        if pmin is None:
            if resource in profile_methods:
                firm_generation += summed_profiles[resource]
            else:
                summed_pmin = plant.Pmin.loc[base_plant_ids_by_type[resource]].sum()
                firm_generation += pd.Series(summed_pmin, index=summed_demand.index)
        else:
            summed_pmin = pmin * plant.Pmax.loc[base_plant_ids_by_type[resource]].sum()
            firm_generation += pd.Series(summed_pmin, index=summed_demand.index)
    # Add plants with plant-level overrides
    for plant_id, pmin in pmin_by_id.items():
        if pmin == 0:
            continue
        if pmin is None:
            if plant.loc[plant_id, "type"] in profile_methods:
                firm_generation += all_profiles[plant_id]
            else:
                plant_pmin = plant.loc[plant_id, "Pmin"]
                firm_generation += pd.Series(plant_pmin, index=summed_demand.index)
        else:
            plant_pmin = plant.loc[plant_id, "Pmax"] * pmin
            firm_generation += pd.Series(plant_pmin, index=summed_demand.index)

    # Finally, compare this summed firm generation against summed curtailable generation
    total_curtailable = summed_profiles[curtailable].sum(axis=1)
    net_demand = summed_demand - firm_generation
    curtailable_max_gen = pd.concat([net_demand, total_curtailable], axis=1).min(axis=1)
    curtailment_fraction = 1 - curtailable_max_gen.sum() / total_curtailable.sum()
    return curtailment_fraction
