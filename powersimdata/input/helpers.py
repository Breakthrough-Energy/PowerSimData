import os

import pandas as pd


def csv_to_data_frame(data_loc, filename):
    """Reads CSV.

    :return: (*pandas.DataFrame*) -- created data frame.
    """
    print("Reading %s" % filename)
    data_frame = pd.read_csv(
        os.path.join(data_loc, filename), index_col=0, float_precision="high"
    )
    return data_frame


def add_column_to_data_frame(data_frame, column_dict):
    """Adds column(s) to data frame. Done inplace.

    :param pandas.DataFrame data_frame: input data frame
    :param dict column_dict: column to be added. Keys are column name and
        values a list of of values.
    """
    for key, value in column_dict.items():
        data_frame[key] = value


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
    add_column_to_data_frame(grid.bus, extra_col_bus)

    extra_col_plant = {
        "lat": get_lat(grid.plant.bus_id),
        "lon": get_lon(grid.plant.bus_id),
    }
    add_column_to_data_frame(grid.plant, extra_col_plant)

    extra_col_branch = {
        "from_lat": get_lat(grid.branch.from_bus_id),
        "from_lon": get_lon(grid.branch.from_bus_id),
        "to_lat": get_lat(grid.branch.to_bus_id),
        "to_lon": get_lon(grid.branch.to_bus_id),
    }
    add_column_to_data_frame(grid.branch, extra_col_branch)


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
    add_column_to_data_frame(grid.plant, extra_col_plant)

    extra_col_branch = {
        "from_zone_id": get_zone_id(grid.branch.from_bus_id),
        "to_zone_id": get_zone_id(grid.branch.to_bus_id),
        "from_zone_name": get_zone_name(grid.branch.from_bus_id),
        "to_zone_name": get_zone_name(grid.branch.to_bus_id),
    }
    add_column_to_data_frame(grid.branch, extra_col_branch)


def add_interconnect_to_grid_data_frames(grid):
    """Adds interconnect name to bus, branch, plant and dcline data frames of
        grid instance.

    :param powersimdata.input.grid.Grid grid: grid instance.
    """
    bus2interconnect = grid.bus2sub.interconnect.to_dict()

    def get_interconnect(idx):
        return [bus2interconnect[i] for i in idx]

    extra_col_bus = {"interconnect": get_interconnect(grid.bus.index)}
    add_column_to_data_frame(grid.bus, extra_col_bus)

    extra_col_branch = {"interconnect": get_interconnect(grid.branch.from_bus_id)}
    add_column_to_data_frame(grid.branch, extra_col_branch)

    extra_col_plant = {"interconnect": get_interconnect(grid.plant.bus_id)}
    add_column_to_data_frame(grid.plant, extra_col_plant)

    extra_col_gencost = {"interconnect": get_interconnect(grid.plant.bus_id)}
    add_column_to_data_frame(grid.gencost["before"], extra_col_gencost)
    add_column_to_data_frame(grid.gencost["after"], extra_col_gencost)

    extra_col_dcline = {
        "from_interconnect": get_interconnect(grid.dcline.from_bus_id),
        "to_interconnect": get_interconnect(grid.dcline.to_bus_id),
    }
    add_column_to_data_frame(grid.dcline, extra_col_dcline)
