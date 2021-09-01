from powersimdata.design.compare.helpers import _reindex_as_necessary
from powersimdata.input.check import _check_data_frame, _check_grid_type


def calculate_branch_difference(branch1, branch2):
    """Calculate the capacity differences between two branch data frames. If capacity in
    ``branch2`` is larger than capacity in ``branch1``, the return will be positive.

    :param pandas.DataFrame branch1: first branch data frame.
    :param pandas.DataFrame branch2: second branch data frame.
    :param float/int difference_threshold: drop any changes less than this value from
        the returned Series.
    :return: (*pandas.Series*) -- capacity difference between the two branch data
        frames.
    """
    _check_data_frame(branch1, "branch1")
    _check_data_frame(branch2, "branch2")
    if not ("rateA" in branch1.columns) and ("rateA" in branch2.columns):
        raise ValueError("branch1 and branch2 both must have 'rateA' columns")
    branch1, branch2 = _reindex_as_necessary(
        branch1, branch2, ["from_bus_id", "to_bus_id"]
    )
    branch_merge = branch1.merge(
        branch2, how="outer", right_index=True, left_index=True, suffixes=(None, "_2")
    )
    branch_merge["diff"] = branch_merge.rateA_2.fillna(0) - branch_merge.rateA.fillna(0)
    # Ensure that lats & lons get filled in as necessary from branch2 entries
    for l in ["from_lat", "from_lon", "to_lat", "to_lon"]:
        branch_merge[l].fillna(branch_merge[f"{l}_2"], inplace=True)

    return branch_merge


def calculate_dcline_difference(grid1, grid2):
    """Calculate capacity differences between dcline tables, and add to/from lat/lon.

    :param powersimdata.input.grid.Grid grid1: first grid instance.
    :param powersimdata.input.grid.Grid grid2: second grid instance.
    :return: (*pandas.DataFrame*) -- data frame with all indices, plus new columns:
        diff, from_lat, from_lon, to_lat, to_lon.
    """
    _check_grid_type(grid1)
    _check_grid_type(grid2)
    dcline1, dcline2 = _reindex_as_necessary(
        grid1.dcline, grid2.dcline, ["from_bus_id", "to_bus_id"]
    )
    # Get latitudes and longitudes for to & from buses
    for dcline, grid in [(dcline1, grid1), (dcline2, grid2)]:
        dcline["from_lat"] = grid.bus.loc[dcline.from_bus_id, "lat"].to_numpy()
        dcline["from_lon"] = grid.bus.loc[dcline.from_bus_id, "lon"].to_numpy()
        dcline["to_lat"] = grid.bus.loc[dcline.to_bus_id, "lat"].to_numpy()
        dcline["to_lon"] = grid.bus.loc[dcline.to_bus_id, "lon"].to_numpy()
    dc_merge = dcline1.merge(
        dcline2, how="outer", right_index=True, left_index=True, suffixes=(None, "_2")
    )
    dc_merge["diff"] = dc_merge.Pmax_2.fillna(0) - dc_merge.Pmax.fillna(0)
    # Ensure that lats & lons get filled in as necessary from grid2.dcline entries
    for l in ["from_lat", "from_lon", "to_lat", "to_lon"]:
        dc_merge[l].fillna(dc_merge[f"{l}_2"], inplace=True)

    return dc_merge
