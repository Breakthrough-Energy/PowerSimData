import copy
import warnings

import numpy as np
import pandas as pd
from scipy.io import savemat

from powersimdata import Grid
from powersimdata.input.transform_profile import TransformProfile

PYPSA_AVAILABLE = True
try:
    import pypsa
except ImportError:
    PYPSA_AVAILABLE = False


pypsa_const = {
    "bus": {
        "rename": {
            "lat": "y",
            "lon": "x",
            "baseKV": "v_nom",
            "type": "control",
            "Gs": "g_pu",
            "Bs": "b_pu",
        },
        "rename_t": {
            "Pd": "p",
            "Qd": "q",
            "Vm": "v_mag_pu",
            "Va": "v_ang",
        },
        "default_drop_cols": [
            "Vmax",
            "Vmin",
            "lam_P",
            "lam_Q",
            "mu_Vmax",
            "mu_Vmin",
            "GenFuelCost",
        ],
    },
    "generator": {
        "rename": {
            "bus_id": "bus",
            "Pmax": "p_nom",
            "Pmin": "p_min_pu",
            "startup_cost": "start_up_cost",
            "shutdown_cost": "shut_down_cost",
            "ramp_30": "ramp_limit",
            "type": "carrier",
        },
        "rename_t": {
            "Pg": "p",
            "Qg": "q",
            "status": "status",
        },
        "default_drop_cols": [
            "ramp_10",
            "mu_Pmax",
            "mu_Pmin",
            "mu_Qmax",
            "mu_Qmin",
            "ramp_agc",
            "Pc1",
            "Pc2",
            "Qc1min",
            "Qc1max",
            "Qc2min",
            "Qc2max",
            "GenIOB",
            "GenIOC",
            "GenIOD",
        ],
    },
    "cost": {
        "rename": {
            "startup": "startup_cost",
            "shutdown": "shutdown_cost",
        }
    },
    "branch": {
        "rename": {
            "from_bus_id": "bus0",
            "to_bus_id": "bus1",
            "rateA": "s_nom",
            "ratio": "tap_ratio",
            "x": "x_pu",
            "r": "r_pu",
            "g": "g_pu",
            "b": "b_pu",
        },
        "rename_t": {
            "Pf": "p0",
            "Qf": "q0",
            "Pt": "p1",
            "Qt": "q1",
        },
        "default_drop_cols": [
            "rateB",
            "rateC",
            "mu_St",
            "mu_angmin",
            "mu_angmax",
        ],
    },
    "link": {
        "rename": {
            "from_bus_id": "bus0",
            "to_bus_id": "bus1",
            "rateA": "s_nom",
            "ratio": "tap_ratio",
            "x": "x_pu",
            "r": "r_pu",
            "g": "g_pu",
            "b": "b_pu",
            "Pmin": "p_min_pu",
            "Pmax": "p_nom",
        },
        "rename_t": {
            "Pf": "p0",
            "Qf": "q0",
            "Pt": "p1",
            "Qt": "q1",
        },
        "default_drop_cols": [
            "QminF",
            "QmaxF",
            "QminT",
            "QmaxT",
            "muPmin",
            "muPmax",
            "muQminF",
            "muQmaxF",
            "muQminT",
            "muQmaxT",
        ],
    },
}


def export_case_mat(grid, filepath=None, storage_filepath=None):
    """Export a grid to a format suitable for loading into simulation engine.
    If optional filepath arguments are used, the results will also be saved to
    the filepaths provided

    :param powersimdata.input.grid.Grid grid: Grid instance.
    :param str filepath: path where main grid file will be saved, if present
    :param str storage_filepath: path where storage data file will be saved, if present.
    :return: (*tuple*) -- the mpc data as a dictionary and the mpc storage data
        as a dictionary, if present. The storage data will be None if not present.
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
    mpc_storage = None

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

    if filepath is not None:
        savemat(filepath, mpc, appendmat=False)
        if mpc_storage is not None:
            savemat(storage_filepath, mpc_storage, appendmat=False)

    return mpc, mpc_storage


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


def export_to_pypsa(
    scenario_or_grid,
    add_all_columns=False,
    add_substations=False,
    add_load_shedding=True,
):
    """Export a Scenario/Grid instance to a PyPSA network.

    .. note::
        This function does not export storages yet.

    :param powersimdata.scenario.scenario.Scenario/
        powersimdata.input.grid.Grid scenario_or_grid: input object. If a Grid instance
        is passed, operational values will be used for the single snapshot "now".
        If a Scenario instance is passed, all available time-series will be
        imported.
    :param bool add_all_columns: whether to add all columns of the
        corresponding component. If true, this will also import columns
        that PyPSA does not process. The default is False.
    :param bool add_substations: whether to export substations. If set
        to True, artificial links of infinite capacity are added from each bus
        to its substation. This is necessary as the substations are imported
        as regualar buses in pypsa and thus require a connection to the network.
        If set to False, the substations will not be exported. This is
        helpful when there are no branches or dclinks connecting the
        substations. Note that the voltage level of the substation buses is set
        to the first bus connected to that substation. The default is False.
    :param bool add_load_shedding: whether to add artificial load shedding
        generators to the exported pypsa network. This ensures feasibility when
        optimizing the exported pypsa network as is. The default is True.
    """
    from powersimdata.scenario.scenario import Scenario  # avoid circular import

    if not PYPSA_AVAILABLE:
        raise ImportError("PyPSA is not installed.")

    if isinstance(scenario_or_grid, Grid):
        grid = scenario_or_grid
        scenario = None
    elif isinstance(scenario_or_grid, Scenario):
        grid = scenario_or_grid.get_grid()
        scenario = scenario_or_grid
    else:
        raise TypeError(
            "Expected type powersimdata.Grid or powersimdata.Scenario, "
            f"get {type(scenario)}."
        )

    drop_cols = []

    # BUS, LOAD & SUBSTATION
    bus_rename = pypsa_const["bus"]["rename"]
    bus_rename_t = pypsa_const["bus"]["rename_t"]

    if not add_all_columns:
        drop_cols = pypsa_const["bus"]["default_drop_cols"]
        if scenario:
            drop_cols += list(bus_rename_t)

    buses = grid.bus.rename(columns=bus_rename)
    buses.control.replace([1, 2, 3, 4], ["PQ", "PV", "slack", ""], inplace=True)
    buses["zone_name"] = buses.zone_id.map({v: k for k, v in grid.zone2id.items()})
    buses["substation"] = "sub" + grid.bus2sub["sub_id"].astype(str)

    # ensure compatibility with substations (these are imported later)
    buses["is_substation"] = False
    buses["interconnect_sub_id"] = -1
    buses["name"] = ""

    loads = {"proportionality_factor": buses["Pd"]}

    shunts = {k: buses.pop(k) for k in ["b_pu", "g_pu"]}

    substations = grid.sub.copy().rename(columns={"lat": "y", "lon": "x"})
    substations.index = "sub" + substations.index.astype(str)
    substations["is_substation"] = True
    substations["substation"] = substations.index
    v_nom = buses.groupby("substation").v_nom.first().reindex(substations.index)
    substations["v_nom"] = v_nom

    buses = buses.drop(columns=drop_cols, errors="ignore").sort_index(axis=1)

    # now time-dependent
    if scenario:
        buses_t = {}
        loads_t = {"p_set": scenario.get_bus_demand()}
    else:
        buses_t = {v: buses.pop(k).to_frame("now").T for k, v in bus_rename_t.items()}
        buses_t["v_ang"] = np.deg2rad(buses_t["v_ang"])

        loads_t = {"p": buses_t.pop("p"), "q": buses_t.pop("q")}

    # GENERATOR & COSTS
    generator_rename = pypsa_const["generator"]["rename"]
    generator_rename_t = pypsa_const["generator"]["rename_t"]

    if not add_all_columns:
        drop_cols = pypsa_const["generator"]["default_drop_cols"]
        if scenario:
            drop_cols += list(generator_rename_t)

    generators = grid.plant.rename(columns=generator_rename)
    generators.p_min_pu /= generators.p_nom.where(generators.p_nom != 0, 1)
    generators["committable"] = np.where(generators.p_min_pu > 0, True, False)
    generators["ramp_limit_down"] = generators.ramp_limit.replace(0, np.nan)
    generators["ramp_limit_up"] = generators.ramp_limit.replace(0, np.nan)
    generators.drop(columns=drop_cols + ["ramp_limit"], inplace=True)

    gencost = grid.gencost["before"]
    gencost = gencost.rename(columns=pypsa_const["cost"]["rename"])
    # Linearize quadratic curves as applicable
    fixed = grid.plant["Pmin"] == grid.plant["Pmax"]
    linearized = gencost.loc[~fixed, "c1"] + gencost.loc[~fixed, "c2"] * (
        grid.plant.loc[~fixed, "Pmax"] + grid.plant.loc[~fixed, "Pmin"]
    )
    gencost["marginal_cost"] = linearized.combine_first(gencost["c1"])
    gencost = gencost[pypsa_const["cost"]["rename"].values()]

    carriers = pd.DataFrame(index=generators.carrier.unique(), dtype=object)

    cars = carriers.index
    constants = grid.model_immutables.plants
    carriers["color"] = pd.Series(constants["type2color"]).reindex(cars)
    carriers["nice_name"] = pd.Series(constants["type2label"]).reindex(cars)
    carriers["co2_emissions"] = pd.Series(constants["carbon_per_mwh"]).reindex(cars)

    # now time-dependent
    if scenario:
        dfs = [scenario.get_wind(), scenario.get_solar(), scenario.get_hydro()]
        p_max_pu = pd.concat(dfs, axis=1)
        p_nom = generators.p_nom[p_max_pu.columns]
        p_max_pu = p_max_pu / p_nom.where(p_nom != 0, 1)
        generators_t = {"p_max_pu": p_max_pu}
        # drop p_nom_min of renewables, make them non-committable
        generators.loc[p_max_pu.columns, "p_min_pu"] = 0
        generators.loc[p_max_pu.columns, "committable"] = False
    else:
        generators_t = {
            v: generators.pop(k).to_frame("now").T
            for k, v in generator_rename_t.items()
        }

    # BRANCHES
    branch_rename = pypsa_const["branch"]["rename"]
    branch_rename_t = pypsa_const["branch"]["rename_t"]

    if not add_all_columns:
        drop_cols = pypsa_const["branch"]["default_drop_cols"]
        if scenario:
            drop_cols += list(branch_rename_t)

    branches = grid.branch.rename(columns=branch_rename).drop(columns=drop_cols)
    branches["v_nom"] = branches.bus0.map(buses.v_nom)
    # BE model assumes a 100 MVA base, pypsa "assumes" a 1 MVA base
    branches[["x_pu", "r_pu"]] /= 100
    branches["x"] = branches.x_pu * branches.v_nom**2
    branches["r"] = branches.r_pu * branches.v_nom**2

    lines = branches.query("branch_device_type == 'Line'")
    lines = lines.drop(columns="branch_device_type")

    transformers = branches.query(
        "branch_device_type in ['TransformerWinding', 'Transformer']"
    )
    transformers = transformers.drop(columns="branch_device_type")

    if scenario:
        lines_t = {}
        transformers_t = {}
    else:
        lines_t = {
            v: lines.pop(k).to_frame("now").T for k, v in branch_rename_t.items()
        }
        transformers_t = {
            v: transformers.pop(k).to_frame("now").T for k, v in branch_rename_t.items()
        }

    # DC LINES
    link_rename = pypsa_const["link"]["rename"]
    link_rename_t = pypsa_const["link"]["rename_t"]

    if not add_all_columns:
        drop_cols = pypsa_const["link"]["default_drop_cols"]
        if scenario:
            drop_cols += list(link_rename_t)

    links = grid.dcline.rename(columns=link_rename).drop(columns=drop_cols)
    links.p_min_pu /= links.p_nom.where(links.p_nom != 0, 1)

    # SUBSTATION CONNECTORS
    sublinks = dict(
        bus0=buses.index, bus1=buses.substation.values, p_nom=np.inf, p_min_pu=-1
    )
    index = "sub" + pd.RangeIndex(len(buses)).astype(str)
    sublinks = pd.DataFrame(sublinks, index=index)

    if scenario:
        links_t = {}
    else:
        links_t = {v: links.pop(k).to_frame("now").T for k, v in link_rename_t.items()}

    # TODO: add storage export
    if not grid.storage["gen"].empty:
        warnings.warn("The export of storages are not implemented yet.")

    # Import everything to a new pypsa network
    n = pypsa.Network()
    if scenario:
        n.snapshots = loads_t["p_set"].index
    n.madd("Bus", buses.index, **buses, **buses_t)
    n.madd("Load", buses.index, bus=buses.index, **loads, **loads_t)
    n.madd("ShuntImpedance", buses.index, bus=buses.index, **shunts)
    n.madd("Generator", generators.index, **generators, **gencost, **generators_t)
    n.madd("Carrier", carriers.index, **carriers)
    n.madd("Line", lines.index, **lines, **lines_t)
    n.madd("Transformer", transformers.index, **transformers, **transformers_t)
    n.madd("Link", links.index, **links, **links_t)

    if add_substations:
        n.madd("Bus", substations.index, **substations)
        n.madd("Link", sublinks.index, **sublinks)

    if add_load_shedding:
        # Load shedding is moddelled by very costy generators whos power output
        # is measured in kW (see the factor `sign`). This keeps the coefficient
        # range in the LOPF low.
        n.madd(
            "Generator",
            buses.index,
            suffix=" load shedding",
            bus=buses.index,
            sign=1e-3,
            marginal_cost=1e2,
            p_nom=1e9,
            carrier="load",
        )
        n.add("Carrier", "load", nice_name="Load Shedding", color="red")

    return n
