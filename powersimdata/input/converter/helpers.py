import pandas as pd


def add_coord_to_grid_data_frames(grid):
    """Adds longitude and latitude information to bus, plant and branch data
    frames of grid instance.

    :param powersimdata.input.grid.Grid grid: grid instance.
    """
    bus2coord = (
        pd.merge(grid.bus2sub[["sub_id"]], grid.sub[["lat", "lon"]], on="sub_id")
        .set_index(grid.bus2sub.index)
        .drop(columns="sub_id")
        .to_dict()
    )

    def get_lat(idx):
        return [bus2coord["lat"][i] for i in idx]

    def get_lon(idx):
        return [bus2coord["lon"][i] for i in idx]

    extra_col_bus = {"lat": get_lat(grid.bus.index), "lon": get_lon(grid.bus.index)}
    grid.bus = grid.bus.assign(**extra_col_bus)

    extra_col_plant = {
        "lat": get_lat(grid.plant.bus_id),
        "lon": get_lon(grid.plant.bus_id),
    }
    grid.plant = grid.plant.assign(**extra_col_plant)

    extra_col_branch = {
        "from_lat": get_lat(grid.branch.from_bus_id),
        "from_lon": get_lon(grid.branch.from_bus_id),
        "to_lat": get_lat(grid.branch.to_bus_id),
        "to_lon": get_lon(grid.branch.to_bus_id),
    }
    grid.branch = grid.branch.assign(**extra_col_branch)


def add_zone_to_grid_data_frames(grid):
    """Adds zone name/id to plant and branch data frames of grid instance.

    :param powersimdata.input.grid.Grid grid: grid instance.
    """
    bus2zone = grid.bus.zone_id.to_dict()

    def get_zone_id(idx):
        return [bus2zone[i] for i in idx]

    def get_zone_name(idx):
        return [grid.id2zone[bus2zone[i]] for i in idx]

    extra_col_plant = {
        "zone_id": get_zone_id(grid.plant.bus_id),
        "zone_name": get_zone_name(grid.plant.bus_id),
    }
    grid.plant = grid.plant.assign(**extra_col_plant)

    extra_col_branch = {
        "from_zone_id": get_zone_id(grid.branch.from_bus_id),
        "to_zone_id": get_zone_id(grid.branch.to_bus_id),
        "from_zone_name": get_zone_name(grid.branch.from_bus_id),
        "to_zone_name": get_zone_name(grid.branch.to_bus_id),
    }
    grid.branch = grid.branch.assign(**extra_col_branch)


def add_interconnect_to_grid_data_frames(grid):
    """Adds interconnect name to bus, branch, plant and dcline data frames of
    grid instance.

    :param powersimdata.input.grid.Grid grid: grid instance.
    """
    bus2interconnect = grid.bus2sub.interconnect.to_dict()

    def get_interconnect(idx):
        return [bus2interconnect[i] for i in idx]

    extra_col_bus = {"interconnect": get_interconnect(grid.bus.index)}
    grid.bus = grid.bus.assign(**extra_col_bus)

    extra_col_branch = {"interconnect": get_interconnect(grid.branch.from_bus_id)}
    grid.branch = grid.branch.assign(**extra_col_branch)

    extra_col_plant = {"interconnect": get_interconnect(grid.plant.bus_id)}
    grid.plant = grid.plant.assign(**extra_col_plant)

    extra_col_gencost = {"interconnect": get_interconnect(grid.plant.bus_id)}
    grid.gencost["before"] = grid.gencost["before"].assign(**extra_col_gencost)
    grid.gencost["after"] = grid.gencost["after"].assign(**extra_col_gencost)

    extra_col_dcline = {
        "from_interconnect": get_interconnect(grid.dcline.from_bus_id),
        "to_interconnect": get_interconnect(grid.dcline.to_bus_id),
    }
    grid.dcline = grid.dcline.assign(**extra_col_dcline)
