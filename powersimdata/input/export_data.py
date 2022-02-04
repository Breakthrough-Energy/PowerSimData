import copy

import numpy as np
from scipy.io import savemat

from powersimdata.input.transform_profile import TransformProfile


def export_case_mat(grid, filepath, storage_filepath=None):
    """Export a grid to a format suitable for loading into simulation engine.

    :param powersimdata.input.grid.Grid grid: Grid instance.
    :param str filepath: path where main grid file will be saved.
    :param str storage_filepath: path where storage data file will be saved, if present.
    """
    grid = copy.deepcopy(grid)

    mpc = {"mpc": {"version": "2", "baseMVA": 100.0}}

    # zone
    mpc["mpc"]["zone"] = np.array(list(grid.id2zone.items()), dtype=object)

    # sub
    sub = grid.sub.copy()
    subid = sub.index.values[np.newaxis].T
    mpc["mpc"]["sub"] = sub.values
    mpc["mpc"]["subid"] = subid

    # bus
    bus = grid.bus.copy()
    busid = bus.index.values[np.newaxis].T
    bus.reset_index(level=0, inplace=True)
    bus.drop(columns=["interconnect", "lat", "lon"], inplace=True)
    mpc["mpc"]["bus"] = bus.values
    mpc["mpc"]["busid"] = busid

    # bus2sub
    bus2sub = grid.bus2sub.copy()
    mpc["mpc"]["bus2sub"] = bus2sub.values

    # plant
    gen = grid.plant.copy()
    genid = gen.index.values[np.newaxis].T
    genfuel = gen.type.values[np.newaxis].T
    genfuelcost = gen.GenFuelCost.values[np.newaxis].T
    heatratecurve = gen[["GenIOB", "GenIOC", "GenIOD"]].values
    gen.reset_index(inplace=True, drop=True)
    gen.drop(
        columns=[
            "type",
            "interconnect",
            "lat",
            "lon",
            "zone_id",
            "zone_name",
            "GenFuelCost",
            "GenIOB",
            "GenIOC",
            "GenIOD",
        ],
        inplace=True,
    )
    mpc["mpc"]["gen"] = gen.values
    mpc["mpc"]["genid"] = genid
    mpc["mpc"]["genfuel"] = genfuel
    mpc["mpc"]["genfuelcost"] = genfuelcost
    mpc["mpc"]["heatratecurve"] = heatratecurve
    # branch
    branch = grid.branch.copy()
    branchid = branch.index.values[np.newaxis].T
    branchdevicetype = branch.branch_device_type.values[np.newaxis].T
    branch.reset_index(inplace=True, drop=True)
    branch.drop(
        columns=[
            "interconnect",
            "from_lat",
            "from_lon",
            "to_lat",
            "to_lon",
            "from_zone_id",
            "to_zone_id",
            "from_zone_name",
            "to_zone_name",
            "branch_device_type",
        ],
        inplace=True,
    )
    mpc["mpc"]["branch"] = branch.values
    mpc["mpc"]["branchid"] = branchid
    mpc["mpc"]["branchdevicetype"] = branchdevicetype

    # generation cost
    gencost = grid.gencost.copy()
    gencost["before"].reset_index(inplace=True, drop=True)
    gencost["before"].drop(columns=["interconnect"], inplace=True)
    mpc["mpc"]["gencost"] = gencost["before"].values

    # DC line
    if len(grid.dcline) > 0:
        dcline = grid.dcline.copy()
        dclineid = dcline.index.values[np.newaxis].T
        dcline.reset_index(inplace=True, drop=True)
        dcline.drop(columns=["from_interconnect", "to_interconnect"], inplace=True)
        mpc["mpc"]["dcline"] = dcline.values
        mpc["mpc"]["dclineid"] = dclineid

    # energy storage
    if len(grid.storage["gen"]) > 0:
        storage = grid.storage.copy()

        mpc_storage = {
            "storage": {
                "xgd_table": np.array([]),
                "gen": np.array(storage["gen"].values, dtype=np.float64),
                "sd_table": {
                    "colnames": storage["StorageData"].columns.values[np.newaxis],
                    "data": storage["StorageData"].values,
                },
            }
        }

        savemat(storage_filepath, mpc_storage, appendmat=False)

    savemat(filepath, mpc, appendmat=False)


def export_transformed_profile(kind, scenario_info, grid, ct, filepath, slice=True):
    """Apply transformation to the given kind of profile and save the result locally.

    :param str kind: which profile to export. This parameter is passed to
        :meth:`TransformProfile.get_profile`.
    :param dict scenario_info: a dict containing the profile version, with
        key in the form base_{kind}
    :param powersimdata.input.grid.Grid grid: a Grid object previously
        transformed.
    :param dict ct: change table.
    :param str filepath: path to save the result, including the filename
    :param bool slice: whether to slice the profiles by the Scenario's time range.
    """
    tp = TransformProfile(scenario_info, grid, ct, slice)
    profile = tp.get_profile(kind)
    print(f"Writing scaled {kind} profile to {filepath} on local machine")
    profile.to_csv(filepath)
