import numpy as np
import pandas as pd

from powersimdata.input.const.pypsa_const import pypsa_const
from powersimdata.input.grid import Grid
from powersimdata.scenario.scenario import Scenario
from powersimdata.utility.helpers import _check_import


def restore_original_columns(df, overwrite=None):
    """Restore original columns in data frame

    :param pandas.DataFrame df: data frame to modify.
    :param list/set/tuple overwrite: array of column(s) in ``df`` to overwrite.
    :return: (*pandas.DataFrame*) -- data frame with original columns.
    """
    if not overwrite:
        overwrite = []
    prefix = "pypsa_"
    for col in df.columns[df.columns.str.startswith(prefix)]:
        target = col[len(prefix) :]
        fallback = df.pop(col)
        if target not in df or target in overwrite:
            df[target] = fallback
    return df


def export_to_pypsa(
    scenario_or_grid,
    add_all_columns=False,
    add_substations=False,
    add_load_shedding=True,
):
    """Export a Scenario/Grid instance to a PyPSA network.

    :param powersimdata.scenario.scenario.Scenario/powersimdata.input.grid.Grid
        scenario_or_grid: input object. If a Grid instance is passed, operational
        values will be used for the single snapshot "now". If a Scenario instance is
        passed, all available time-series will be imported.
    :param bool add_all_columns: whether to add all columns of the corresponding
        component. If true, this will also import columns that PyPSA does not process.
        The default is False.
    :param bool add_substations: whether to export substations. If set to True,
        artificial links of infinite capacity are added from each bus to its
        substation. This is necessary as the substations are imported as regualar buses in pypsa and thus require a connection to the network. If set to False, the
        substations will not be exported. This is helpful when there are no branches or
        dclinks connecting the substations. Note that the voltage level of the
        substation buses is set to the first bus connected to that substation. The
        default is False.
    :param bool add_load_shedding: whether to add artificial load shedding generators
        to the exported pypsa network. This ensures feasibility when optimizing the
        exported pypsa network as is. The default is True.
    :return: (*pypsa.components.Network*) -- the exported Network object.
    :raises TypeError: if ``scenario_or_grid`` is not a Grid/Scenario object.
    """
    pypsa = _check_import("pypsa")

    if isinstance(scenario_or_grid, Grid):
        grid = scenario_or_grid
        scenario = None
    elif isinstance(scenario_or_grid, Scenario):
        grid = scenario_or_grid.get_grid()
        scenario = scenario_or_grid
    else:
        raise TypeError(
            "Expected type powersimdata.Grid or powersimdata.Scenario, "
            f"got {type(scenario_or_grid)}."
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
    buses.control.replace([1, 2, 3, 4], ["PQ", "PV", "Slack", ""], inplace=True)
    buses["zone_name"] = buses.zone_id.map({v: k for k, v in grid.zone2id.items()})
    buses["substation"] = "sub" + grid.bus2sub["sub_id"].astype(str)

    # ensure compatibility with substations (these are imported later)
    buses["is_substation"] = False
    buses["interconnect_sub_id"] = -1
    buses["name"] = ""

    loads = {"proportionality_factor": buses["Pd"]}

    shunts = pd.DataFrame({k: buses.pop(k) for k in ["b_pu", "g_pu"]})
    shunts = shunts.dropna(how="all")

    substations = grid.sub.copy().rename(columns={"lat": "y", "lon": "x"})
    substations.index = "sub" + substations.index.astype(str)
    substations["is_substation"] = True
    substations["substation"] = substations.index
    v_nom = buses.groupby("substation").v_nom.first().reindex(substations.index)
    substations["v_nom"] = v_nom

    buses = buses.drop(columns=drop_cols, errors="ignore").sort_index(axis=1)
    buses = restore_original_columns(buses)

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

    gencost = grid.gencost["before"].copy()
    # Linearize quadratic curves as applicable
    fixed = grid.plant["Pmin"] == grid.plant["Pmax"]
    linearized = gencost.loc[~fixed, "c1"] + gencost.loc[~fixed, "c2"] * (
        grid.plant.loc[~fixed, "Pmax"] + grid.plant.loc[~fixed, "Pmin"]
    )
    gencost["c1"] = linearized.combine_first(gencost["c1"])
    gencost = gencost.rename(columns=pypsa_const["gencost"]["rename"])
    gencost = gencost[pypsa_const["gencost"]["rename"].values()]

    generators = generators.assign(**gencost)
    generators = restore_original_columns(generators)

    carriers = pd.DataFrame(index=generators.carrier.unique(), dtype=object)

    cars = carriers.index
    if grid.model_immutables is not None:
        constants = grid.model_immutables.plants
        carriers["color"] = pd.Series(constants["type2color"]).reindex(cars)
        carriers["nice_name"] = pd.Series(constants["type2label"]).reindex(cars)
        carriers["co2_emissions"] = pd.Series(constants["carbon_per_mwh"]).div(
            1e3
        ) * pd.Series(constants["efficiency"]).reindex(cars, fill_value=0)
        generators["efficiency"] = generators.carrier.map(
            constants["efficiency"]
        ).fillna(0)

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
    lines = restore_original_columns(lines)

    transformers = branches.query(
        "branch_device_type in ['TransformerWinding', 'Transformer']"
    )

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
    links = restore_original_columns(links, overwrite=["p_min_pu", "p_max_pu"])

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

    # STORAGES
    # TODO: make distinction to pypsa stores
    storage_data_keys = ["StorageData", "gen", "gencost"]
    storage = []
    defaults = {k: v for k, v in grid.storage.items() if k not in storage_data_keys}
    for k in storage_data_keys:
        rename = pypsa_const["storage_" + k.lower()]["rename"]
        if not add_all_columns:
            drop_cols = pypsa_const["storage_" + k.lower()]["default_drop_cols"]
        df = grid.storage[k].rename(columns=rename).drop(columns=drop_cols)
        storage.append(df)
        defaults = {rename.get(k, k): v for k, v in defaults.items()}

    storage = pd.concat(storage, axis=1)
    storage = storage.loc[:, ~storage.columns.duplicated()]
    for k, v in defaults.items():
        storage[k] = storage[k].fillna(v) if k in storage else v

    storage = restore_original_columns(storage)

    # Import everything to a new pypsa network
    n = pypsa.Network()
    if scenario:
        n.snapshots = loads_t["p_set"].index
    n.madd("Bus", buses.index, **buses, **buses_t)
    n.madd("Load", buses.index, bus=buses.index, **loads, **loads_t)
    n.madd("ShuntImpedance", shunts.index, bus=shunts.index, **shunts)
    n.madd("Generator", generators.index, **generators, **generators_t)
    n.madd("Carrier", carriers.index, **carriers)
    n.madd("Line", lines.index, **lines, **lines_t)
    n.madd("Transformer", transformers.index, **transformers, **transformers_t)
    n.madd("Link", links.index, **links, **links_t)
    n.madd("StorageUnit", storage.index, **storage)

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

    n.name = ", ".join([grid.data_loc] + grid.interconnect)
    return n
