from collections import defaultdict

import pandas as pd

from powersimdata.input.check import (
    _check_areas_are_in_grid_and_format,
    _check_data_frame,
    _check_grid_type,
    _check_plants_are_in_grid,
    _check_resources_are_in_grid_and_format,
)


def get_resources_in_grid(grid):
    """Get resources in grid.

    :param powersimdata.input.grid.Grid grid: a Grid instance.
    :return: (*set*) -- name of all resources in grid.
    """
    _check_grid_type(grid)
    resources = set(grid.plant["type"].unique())
    return resources


def get_active_resources_in_grid(grid):
    """Get active resources in grid.

    :param powersimdata.input.grid.Grid grid: a Grid instance.
    :return: (*set*) -- name of active resources in grid.
    """
    _check_grid_type(grid)
    active_resources = set(grid.plant.loc[grid.plant["Pmax"] > 0].type.unique())
    return active_resources


def get_plant_id_for_resources(resources, grid):
    """Get plant id for plants fueled by resource(s).

    :param str/list/tuple/set resources: name of resource(s).
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*set*) -- list of plant id.
    """
    resources = _check_resources_are_in_grid_and_format(resources, grid)
    plant = grid.plant
    plant_id = plant[(plant.type.isin(resources))].index
    return set(plant_id)


def get_plant_id_in_loadzones(loadzones, grid):
    """Get plant id for plants in loadzone(s).

    :param str/list/tuple/set loadzones: name of load zone(s).
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*set*) -- list of plant id.
    """
    areas = _check_areas_are_in_grid_and_format({"loadzone": loadzones}, grid)
    plant = grid.plant
    plant_id = plant[(plant.zone_name.isin(areas["loadzone"]))].index
    return set(plant_id)


def get_plant_id_in_interconnects(interconnects, grid):
    """Get plant id for plants in interconnect(s).

    :param str/list/tuple/set interconnects: name of interconnect(s).
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*set*) -- list of plant id
    """
    areas = _check_areas_are_in_grid_and_format({"interconnect": interconnects}, grid)
    return set.union(
        *(
            set(grid.plant.groupby("interconnect").groups[i])
            for i in areas["interconnect"]
        )
    )


def get_plant_id_in_states(states, grid):
    """Get plant id for plants in state(s).

    :param str/list/tuple/set states: states(s) name or abbreviation(s).
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*set*) -- list of plant id.
    """
    areas = _check_areas_are_in_grid_and_format({"state": states}, grid)
    loadzones = set.union(
        *(grid.model_immutables.zones["state2loadzone"][i] for i in areas["state"])
    )

    plant = grid.plant
    plant_id = plant[(plant.zone_name.isin(loadzones))].index
    return set(plant_id)


def get_plant_id_for_resources_in_loadzones(resources, loadzones, grid):
    """Get plant id for plants fueled by resource(s) in load zone(s).

    :param str/list/tuple/set resources: name of resource(s).
    :param str/list/tuple/set loadzones: name of load zone(s).
    :param powersimdata.input.grid.Grid grid: a Grid instance.
    :return: (*set*) -- list of plant id.
    """
    plant_id = get_plant_id_for_resources(resources, grid) & get_plant_id_in_loadzones(
        loadzones, grid
    )
    return set(plant_id)


def get_plant_id_for_resources_in_interconnects(resources, interconnects, grid):
    """Get plant id for for plants fueled by resource(s) in interconnect(s).

    :param str/list/tuple/set resources: name of resource(s).
    :param str/list/tuple/set interconnects: name of interconnect(s).
    :param powersimdata.input.grid.Grid grid: a Grid instance.
    :return: (*set*) -- list of plant id.
    """
    plant_id = get_plant_id_for_resources(
        resources, grid
    ) & get_plant_id_in_interconnects(interconnects, grid)
    return set(plant_id)


def get_plant_id_for_resources_in_states(resources, states, grid):
    """Get plant id for for plants fueled by resource(s) in state(s).

    :param str/list/tuple/set resources: name of resource(s).
    :param str/list/tuple/set states: state(s) name or abbreviation.
    :param powersimdata.input.grid.Grid grid: a Grid instance.
    :return: (*set*) -- list of plant id
    """
    plant_id = get_plant_id_for_resources(resources, grid) & get_plant_id_in_states(
        states, grid
    )
    return set(plant_id)


def decompose_plant_data_frame_into_resources(df, resources, grid):
    """Take a plant-column data frame and decompose it into plant-column data frames
    for each resource.

    :param pandas.DataFrame df: data frame, columns are plant id in grid.
    :param str/list/tuple/set resources: resource(s) to use for decomposition.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*dict*) -- keys are resources, values are plant-column data frames.
    """
    _check_data_frame(df, "PG")
    plant_id = set(df.columns)
    _check_plants_are_in_grid(plant_id, grid)
    resources = _check_resources_are_in_grid_and_format(resources, grid)

    df_resources = {
        r: df[list(get_plant_id_for_resources(r, grid) & plant_id)].sort_index(axis=1)
        for r in resources
    }
    return df_resources


def decompose_plant_data_frame_into_areas(df, areas, grid):
    """Take a plant-column data frame and decompose it into plant-column data frames
    for areas.

    :param pandas.DataFrame df: data frame, columns are plant id in grid.
    :param dict areas: areas to use for decomposition. Keys are area types
        ('*loadzone*', '*state*', or '*interconnect*'), values are
        str/list/tuple/set of areas.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*dict*) -- keys are areas, values are plant-column data frames.
    """
    _check_data_frame(df, "PG")
    plant_id = set(df.columns)
    _check_plants_are_in_grid(plant_id, grid)
    areas = _check_areas_are_in_grid_and_format(areas, grid)

    df_areas = {}
    for k, v in areas.items():
        if k == "interconnect":
            for i in v:
                name = "%s interconnect" % " - ".join(i.split("_"))
                df_areas[name] = df[
                    list(get_plant_id_in_interconnects(i, grid) & plant_id)
                ]
        elif k == "state":
            for s in v:
                df_areas[s] = df[list(get_plant_id_in_states(s, grid) & plant_id)]
        elif k == "loadzone":
            for l in v:
                df_areas[l] = df[list(get_plant_id_in_loadzones(l, grid) & plant_id)]

    return df_areas


def decompose_plant_data_frame_into_areas_and_resources(df, areas, resources, grid):
    """Take a plant-column data frame and decompose it into plant-column data frames
    for each resources-areas combinations.

    :param pandas.DataFrame df: data frame, columns are plant id in grid.
    :param dict areas: areas to use for decomposition. Keys are area types
        ('*loadzone*', '*state*' or '*interconnect*'), values are
        str/list/tuple/set of areas.
    :param str/list/tuple/set resources: resource(s) to use for decomposition.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*dict*) -- keys are areas, values are dictionaries whose keys are
        resources and values are data frames indexed by (datetime, plant) where plant
        include only plants of matching type and located in area.
    """
    resources = _check_resources_are_in_grid_and_format(resources, grid)
    df_areas_resources = {
        a: decompose_plant_data_frame_into_resources(df_a, resources, grid)
        for a, df_a in decompose_plant_data_frame_into_areas(df, areas, grid).items()
    }

    return df_areas_resources


def decompose_plant_data_frame_into_resources_and_areas(df, resources, areas, grid):
    """Take a plant-column data frame and decompose it into plant-column data frames
    for each resources-areas combinations.

    :param pandas.DataFrame df: data frame, columns are plant id in grid.
    :param str/list/tuple/set resources: resource(s) to use for decomposition.
    :param dict areas: areas to use for decomposition. Keys are area types
        ('*loadzone*', '*state*', '*state_abv*' or '*interconnect*'), values are
        str/list/tuple/set of areas.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*dict*) -- keys are resources, values are dictionaries whose keys are
        areas and values are data frames indexed by (datetime, plant) where plant
        include only plants of matching type and located in area.
    """
    resources_areas = defaultdict(dict)

    areas_resources = decompose_plant_data_frame_into_areas_and_resources(
        df, areas, resources, grid
    )
    for a in areas_resources.keys():
        for r in areas_resources[a].keys():
            resources_areas[r].update({a: areas_resources[a][r]})

    return resources_areas


def summarize_plant_to_bus(df, grid, all_buses=False):
    """Take a plant-column data frame and sum to a bus-column data frame.

    :param pandas.DataFrame df: dataframe, columns are plant id in grid.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :param boolean all_buses: return all buses in grid, not just plant buses.
    :return: (*pandas.DataFrame*) -- index as df input, columns are buses.
    """
    _check_data_frame(df, "PG")
    _check_grid_type(grid)
    _check_plants_are_in_grid(df.columns.to_list(), grid)

    all_buses_in_grid = grid.plant["bus_id"]
    buses_in_df = all_buses_in_grid.loc[df.columns]
    bus_data = df.T.groupby(buses_in_df).sum().T
    if all_buses:
        bus_data = pd.DataFrame(
            bus_data, columns=grid.bus.index, index=df.index
        ).fillna(0.0)

    return bus_data


def summarize_plant_to_location(df, grid):
    """Take a plant-column data frame and sum to a location-column data frame.

    :param pandas.DataFrame df: dataframe, columns are plant id in grid.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*pandas.DataFrame*) -- index: df index, columns: location tuples.
    """
    _check_data_frame(df, "PG")
    _check_grid_type(grid)
    _check_plants_are_in_grid(df.columns.to_list(), grid)

    all_locations = grid.plant[["lat", "lon"]]
    locations_in_df = all_locations.loc[df.columns].to_records(index=False)
    location_data = df.groupby(locations_in_df, axis=1).sum()

    return location_data


def get_plant_id_for_resources_in_area(scenario, area, resources, area_type=None):
    """Get the list of plant ids of certain resources in the specific area of a
    scenario.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance
    :param str area: one of *loadzone*, *state*, *state abbreviation*,
        *interconnect*, *'all'*
    :param str/list resources: one or a list of resources
    :param str area_type: one of *'loadzone'*, *'state'*, *'state_abbr'*,
        *'interconnect'*
    :return: (*list*) -- list of plant id
    """
    resource_set = set([resources]) if isinstance(resources, str) else set(resources)
    grid = scenario.state.get_grid()
    loadzone_set = grid.model_immutables.area_to_loadzone(area, area_type=area_type)
    plant_id = grid.plant[
        (grid.plant["zone_name"].isin(loadzone_set))
        & (grid.plant["type"].isin(resource_set))
    ].index.tolist()

    return plant_id


def get_storage_id_in_area(scenario, area, area_type=None):
    """Get the list of storage ids in the specific area of a scenario

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance
    :param str area: one of *loadzone*, *state*, *state abbreviation*,
        *interconnect*, *'all'*
    :param str area_type: one of *'loadzone'*, *'state'*, *'state_abbr'*,
        *'interconnect'*
    :return: (*list*) -- list of storage id
    """
    grid = scenario.state.get_grid()
    loadzone_set = grid.model_immutables.area_to_loadzone(area, area_type=area_type)
    loadzone_id_set = {grid.zone2id[lz] for lz in loadzone_set if lz in grid.zone2id}

    gen = grid.storage["gen"]
    storage_id = gen.loc[
        gen["bus_id"].apply(lambda x: grid.bus.loc[x, "zone_id"]).isin(loadzone_id_set)
    ].index.tolist()

    return storage_id
