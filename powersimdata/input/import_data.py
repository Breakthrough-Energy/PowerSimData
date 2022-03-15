import warnings

import numpy as np
import pandas as pd

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.export_data import pypsa_const as pypsa_export_const

pypsa_import_const = {
    "bus": {
        "default_drop_cols": [
            "interconnect_sub_id",
            "is_substation",
            "name",
            "substation",
            "unit",
            "v_mag_pu_max",
            "v_mag_pu_min",
            "v_mag_pu_set",
            "zone_name",
            "carrier",
            "sub_network",
        ]
    },
    "sub": {
        "default_select_cols": [
            "name",
            "interconnect_sub_id",
            "lat",
            "lon",
            "interconnect",
        ]
    },
    "generator": {
        "drop_cols_in_advance": ["type"],
        "default_drop_cols": [
            "build_year",
            "capital_cost",
            "committable",
            "control",
            "down_time_before",
            "efficiency",
            "lifetime",
            "marginal_cost",
            "min_down_time",
            "min_up_time",
            "p_max_pu",
            "p_nom_extendable",
            "p_nom_max",
            "p_nom_min",
            "p_nom_opt",
            "p_set",
            "q_set",
            "ramp_limit_down",
            "ramp_limit_shut_down",
            "ramp_limit_start_up",
            "ramp_limit_up",
            "shutdown_cost",
            "sign",
            "startup_cost",
            "up_time_before",
        ],
    },
    "gencost": {
        "default_select_cols": [
            "type",
            "startup",
            "shutdown",
            "n",
            "c2",
            "c1",
            "c0",
            "interconnect",
        ]
    },
    "branch": {
        # these need to be dropped as they appear in both pypsa and powersimdata but need
        # to be translated at the same time
        "drop_cols_in_advance": [
            "x",
            "r",
            "b",
            "g",
        ],
        "default_drop_cols": [
            "build_year",
            "capital_cost",
            "carrier",
            "g",
            "length",
            "lifetime",
            "model",
            "num_parallel",
            "phase_shift",
            "r_pu_eff",
            "s_max_pu",
            "s_nom_extendable",
            "s_nom_max",
            "s_nom_min",
            "s_nom_opt",
            "sub_network",
            "tap_position",
            "tap_side",
            "terrain_factor",
            "type",
            "v_ang_max",
            "v_ang_min",
            "v_nom",
            "x_pu_eff",
        ],
    },
    "link": {
        "default_drop_cols": [
            "build_year",
            "capital_cost",
            "carrier",
            "efficiency",
            "length",
            "lifetime",
            "marginal_cost",
            "p_max_pu",
            "p_nom_extendable",
            "p_nom_max",
            "p_nom_min",
            "p_nom_opt",
            "p_set",
            "ramp_limit_down",
            "ramp_limit_up",
            "terrain_factor",
            "type",
        ]
    },
}


class FromPyPSA(AbstractGrid):
    """Network reader for PyPSA networks."""

    def __init__(self, network, drop_cols=True):
        """Constructor.

        :param pypsa.Network network: Network to read in.
        """
        super().__init__()
        self._read_network(network, drop_cols=drop_cols)

    def _read_network(self, n, drop_cols=True):

        # INTERCONNECT, BUS, SUB, SHUNTS
        interconnect = n.name.split(", ")
        if len(interconnect) > 1:
            data_loc = interconnect.pop(0)
        else:
            # TODO: How to deal with immutables and data_loc which is not in
            # powersimdata.grid.Grid.SUPPORTED_MODELS?
            data_loc = "usa_tamu"

        df = n.df("Bus").drop(columns="type")
        bus = _translate_df(df, "bus")
        bus["type"] = bus.type.replace(["PQ", "PV", "slack", ""], [1, 2, 3, 4])
        bus.index.name = "bus_id"

        if "zone_id" in n.buses and "zone_name" in n.buses:
            uniques = ~n.buses.zone_id.duplicated() * n.buses.zone_id.notnull()
            zone2id = (
                n.buses[uniques].set_index("zone_name").zone_id.astype(int).to_dict()
            )
            id2zone = _revert_dict(zone2id)
        else:
            zone2id = {}
            id2zone = {}

        if "is_substation" in bus:
            cols = pypsa_import_const["sub"]["default_select_cols"]
            sub = bus[bus.is_substation][cols]
            sub.index = sub[sub.index.str.startswith("sub")].index.str[3:]
            sub.index.name = "sub_id"
            bus = bus[~bus.is_substation]
            bus2sub = bus[["substation", "interconnect"]].copy()
            bus2sub["sub_id"] = pd.to_numeric(
                bus2sub.pop("substation").str[3:], errors="ignore"
            )
        else:
            warnings.warn("Substations could not be parsed.")
            sub = pd.DataFrame()
            bus2sub = pd.DataFrame()

        if not n.shunt_impedances.empty:
            shunts = _translate_df(n.shunt_impedances, "bus")
            bus[["Bs", "Gs"]] = shunts[["Bs", "Gs"]]

        # PLANT & GENCOST
        drop_cols = pypsa_import_const["generator"]["drop_cols_in_advance"]
        df = n.generators.drop(columns=drop_cols)
        plant = _translate_df(df, "generator")
        plant["ramp_30"] = n.generators["ramp_limit_up"].fillna(0)
        plant["Pmin"] *= plant["Pmax"]  # from relative to absolute value
        plant["bus_id"] = pd.to_numeric(plant.bus_id, errors="ignore")
        plant.index.name = "plant_id"

        cols = pypsa_import_const["gencost"]["default_select_cols"]
        gencost = _translate_df(df, "cost")
        gencost = gencost.assign(type=2, n=3, c0=0, c2=0)
        gencost = gencost.reindex(columns=cols)
        gencost.index.name = "plant_id"

        # BRANCHES
        drop_cols = pypsa_import_const["branch"]["drop_cols_in_advance"]
        df = n.lines.drop(columns=drop_cols, errors="ignore")
        lines = _translate_df(df, "branch")
        lines["branch_device_type"] = "Line"

        df = n.transformers.drop(columns=drop_cols, errors="ignore")
        transformers = _translate_df(df, "branch")
        transformers["branch_device_type"] = "Transformer"

        branch = pd.concat([lines, transformers])
        branch["x"] *= 100
        branch["r"] *= 100
        branch["from_bus_id"] = pd.to_numeric(branch.from_bus_id, errors="ignore")
        branch["to_bus_id"] = pd.to_numeric(branch.to_bus_id, errors="ignore")
        branch.index.name = "branch_id"

        # DC LINES
        df = n.df("Link")[lambda df: df.index.str[:3] != "sub"]
        dcline = _translate_df(df, "link")
        dcline["Pmin"] *= dcline["Pmax"]  # convert relative to absolute
        dcline["from_bus_id"] = pd.to_numeric(dcline.from_bus_id, errors="ignore")
        dcline["to_bus_id"] = pd.to_numeric(dcline.to_bus_id, errors="ignore")

        # STORAGES
        if not n.storage_units.empty or not n.stores.empty:
            warnings.warn("The export of storages are not implemented yet.")

        # Drop columns if wanted
        if drop_cols:
            _drop_cols(bus, "bus")
            _drop_cols(plant, "generator")
            _drop_cols(branch, "branch")
            _drop_cols(dcline, "link")

        # Pull operational properties into grid object
        if len(n.snapshots) == 1:
            bus = bus.assign(**_translate_pnl(n.pnl("Bus"), "bus"))
            bus["Va"] = np.rad2deg(bus["Va"])
            bus = bus.assign(**_translate_pnl(n.pnl("Load"), "bus"))
            plant = plant.assign(**_translate_pnl(n.pnl("Generator"), "generator"))
            _ = pd.concat(
                [_translate_pnl(n.pnl(c), "branch") for c in ["Line", "Transformer"]]
            )
            branch = branch.assign(**_)
            dcline = dcline.assign(**_translate_pnl(n.pnl("Link"), "link"))

        # Convert to numeric
        for df in (bus, sub, bus2sub, gencost, plant, branch, dcline):
            df.index = pd.to_numeric(df.index, errors="ignore")

        self.data_loc = data_loc
        self.interconnect = interconnect
        self.bus = bus
        self.sub = sub
        self.bus2sub = bus2sub
        self.branch = branch.sort_index()
        self.dcline = dcline
        self.zone2id = zone2id
        self.id2zone = id2zone
        self.plant = plant
        self.gencost["before"] = gencost
        self.gencost["after"] = gencost


def _drop_cols(df, key):
    cols = pypsa_import_const[key]["default_drop_cols"]
    df.drop(columns=cols, inplace=True, errors="ignore")


def _translate_df(df, key):
    translators = _revert_dict(pypsa_export_const[key]["rename"])
    return df.rename(columns=translators)


def _translate_pnl(pnl, key):
    translators = _revert_dict(pypsa_export_const[key]["rename_t"])
    df = pd.concat(
        {v: pnl[k].iloc[0] for k, v in translators.items() if k in pnl}, axis=1
    )
    return df


def _revert_dict(d):
    return {v: k for (k, v) in d.items()}


def is_pypsa_network(obj):
    """
    Check whether object is a pypsa.Network or not.

    If pypsa is not installed the function returns False.
    """
    from powersimdata.input.export_data import PYPSA_AVAILABLE

    if not PYPSA_AVAILABLE:
        return False
    from pypsa import Network

    return isinstance(obj, Network)
