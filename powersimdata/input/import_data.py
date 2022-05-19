import warnings
from typing import OrderedDict

import numpy as np
import pandas as pd

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.export_data import pypsa_const as pypsa_export_const
from powersimdata.scenario.analyze import Analyze

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
            data_loc = "pypsa"

        df = n.df("Bus").drop(columns="type")
        bus = self._translate_df(df, "bus")
        bus["type"] = bus.type.replace(["PQ", "PV", "slack", ""], [1, 2, 3, 4])
        bus.index.name = "bus_id"

        if "zone_id" in n.buses and "zone_name" in n.buses:
            uniques = ~n.buses.zone_id.duplicated() * n.buses.zone_id.notnull()
            zone2id = (
                n.buses[uniques].set_index("zone_name").zone_id.astype(int).to_dict()
            )
            id2zone = self._revert_dict(zone2id)
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
            shunts = self._translate_df(n.shunt_impedances, "bus")
            bus[["Bs", "Gs"]] = shunts[["Bs", "Gs"]]

        # PLANT & GENCOST
        drop_cols = pypsa_import_const["generator"]["drop_cols_in_advance"]
        df = n.generators.drop(columns=drop_cols)
        plant = self._translate_df(df, "generator")
        plant["ramp_30"] = n.generators["ramp_limit_up"].fillna(0)
        plant["Pmin"] *= plant["Pmax"]  # from relative to absolute value
        plant["bus_id"] = pd.to_numeric(plant.bus_id, errors="ignore")
        plant.index.name = "plant_id"

        cols = pypsa_import_const["gencost"]["default_select_cols"]
        gencost = self._translate_df(df, "cost")
        gencost = gencost.assign(type=2, n=3, c0=0, c2=0)
        gencost = gencost.reindex(columns=cols)
        gencost.index.name = "plant_id"

        # BRANCHES
        drop_cols = pypsa_import_const["branch"]["drop_cols_in_advance"]
        df = n.lines.drop(columns=drop_cols, errors="ignore")
        lines = self._translate_df(df, "branch")
        lines["branch_device_type"] = "Line"

        df = n.transformers.drop(columns=drop_cols, errors="ignore")
        transformers = self._translate_df(df, "branch")
        if "branch_device_type" not in transformers:
            transformers["branch_device_type"] = "Transfomer"

        branch = pd.concat([lines, transformers])
        branch["x"] *= 100
        branch["r"] *= 100
        branch["from_bus_id"] = pd.to_numeric(branch.from_bus_id, errors="ignore")
        branch["to_bus_id"] = pd.to_numeric(branch.to_bus_id, errors="ignore")
        branch.index.name = "branch_id"

        # DC LINES
        df = n.df("Link")[lambda df: df.index.str[:3] != "sub"]
        dcline = self._translate_df(df, "link")
        dcline["Pmin"] *= dcline["Pmax"]  # convert relative to absolute
        dcline["from_bus_id"] = pd.to_numeric(dcline.from_bus_id, errors="ignore")
        dcline["to_bus_id"] = pd.to_numeric(dcline.to_bus_id, errors="ignore")

        # STORAGES
        if not n.storage_units.empty or not n.stores.empty:
            warnings.warn("The export of storages are not implemented yet.")

        # Drop columns if wanted
        if drop_cols:
            self._drop_cols(bus, "bus")
            self._drop_cols(plant, "generator")
            self._drop_cols(branch, "branch")
            self._drop_cols(dcline, "link")

        # Pull operational properties into grid object
        if len(n.snapshots) == 1:
            bus = bus.assign(**self._translate_pnl(n.pnl("Bus"), "bus"))
            bus["Va"] = np.rad2deg(bus["Va"])
            bus = bus.assign(**self._translate_pnl(n.pnl("Load"), "bus"))
            plant = plant.assign(**self._translate_pnl(n.pnl("Generator"), "generator"))
            _ = pd.concat(
                [
                    self._translate_pnl(n.pnl(c), "branch")
                    for c in ["Line", "Transformer"]
                ]
            )
            branch = branch.assign(**_)
            dcline = dcline.assign(**self._translate_pnl(n.pnl("Link"), "link"))
        else:
            plant["status"] = n.generators_t.status.any().astype(int)

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

    def _drop_cols(self, df, key):
        cols = pypsa_import_const[key]["default_drop_cols"]
        df.drop(columns=cols, inplace=True, errors="ignore")

    def _translate_df(self, df, key):
        translators = self._revert_dict(pypsa_export_const[key]["rename"])
        return df.rename(columns=translators)

    def _translate_pnl(self, pnl, key):
        """
        Translate time-dependent dataframes with one time step from pypsa to static dataframes.

        :param str pnl: Name of the time-dependent dataframe.
        :param str key: Correspoding key in the pypsa conversion dictionary `pypsa_export_const`.
        """
        translators = self._revert_dict(pypsa_export_const[key]["rename_t"])
        df = pd.concat(
            {v: pnl[k].iloc[0] for k, v in translators.items() if k in pnl}, axis=1
        )
        return df

    def _revert_dict(self, d):
        return {v: k for (k, v) in d.items()}


class AnalyzePypsa(Analyze):
    """PyPSA Scenario Analyze State."""

    def __init__(self, n):
        """Constructor."""
        # Circumvent cyclic imports
        from pypsa.descriptors import get_switchable_as_dense

        from powersimdata.input.change_table import ChangeTable
        from powersimdata.input.grid import Grid
        from powersimdata.input.import_data import is_pypsa_network

        if not is_pypsa_network(n):
            raise TypeError(f"Expected a pypsa.Network, got {type(n)}.")

        self.base_grid = Grid(n, source="pypsa")
        self.name = n.name
        self.interconnect = self.base_grid.interconnect
        self.grid_model = getattr(self.base_grid, "grid_model", None)
        self.ct = ChangeTable(self.base_grid)
        self.existing = pd.Series(dtype=object)
        self.interconnect = self.base_grid.interconnect
        self._scenario_info = None

        self.start_date = n.snapshots[0]
        self.end_date = n.snapshots[-1]
        self.interval = None

        if not n.loads_t.p.empty:
            demand = n.loads_t.p.copy()
        else:
            demand = n.loads_t.p_set.copy()
        if "zone_id" in n.buses:
            # Assume this is a PyPSA network originally created from powersimdata
            demand = demand.groupby(n.buses.zone_id.dropna().astype(int), axis=1).sum()
        demand.columns = pd.to_numeric(demand.columns, errors="ignore")
        demand.columns.name = None
        demand.index.name = "UTC Time"
        self._demand = demand

        p_max_pu = get_switchable_as_dense(n, "Generator", "p_max_pu")
        p_max_pu.columns = pd.to_numeric(p_max_pu.columns, errors="ignore")
        p_max_pu.columns.name = None
        p_max_pu.index.name = "UTC"

        gens = n.generators.copy()
        gens.index = pd.to_numeric(gens.index, errors="ignore")
        gens.index.name = None

        hydro_gen = gens.query("'hydro' in carrier").index
        self._hydro = p_max_pu[hydro_gen] * gens.p_nom[hydro_gen]

        solar_gen = gens.query("'solar' in carrier").index
        self._solar = p_max_pu[solar_gen] * gens.p_nom[solar_gen]

        wind_gen = gens.query("'wind' in carrier").index
        self._wind = p_max_pu[wind_gen] * gens.p_nom[wind_gen]

        pattern = " load shedding"
        mask = n.generators.index.str.endswith(pattern)
        loadshed_gen = n.generators[mask].index
        loadshed = n.generators_t.p[loadshed_gen] * n.generators.sign[loadshed_gen]
        loadshed_buses = loadshed.columns.str[: -len(pattern)]
        loadshed.columns = pd.to_numeric(loadshed_buses, errors="ignore")

        pg = n.generators_t.p.drop(columns=loadshed_gen)
        pg.columns = pd.to_numeric(pg.columns, errors="ignore")

        pf = pd.concat([n.lines_t.p0, n.transformers_t.p0], axis=1)
        pf.columns = pd.to_numeric(pf.columns, errors="ignore")

        pf_dcline = n.links_t.p0[n.links.query("carrier == 'dc'").index]
        pf_dcline.columns = pd.to_numeric(pf_dcline.columns, errors="ignore")

        lmp = n.buses_t.marginal_price.copy()

        congu = pd.concat([n.lines_t.mu_upper, n.transformers_t.mu_upper], axis=1)
        congu.columns = pd.to_numeric(congu.columns, errors="ignore")

        congl = pd.concat([n.lines_t.mu_lower, n.transformers_t.mu_lower], axis=1)
        congl.columns = pd.to_numeric(congl.columns, errors="ignore")

        average_cong = pd.concat({"CONGL": congl.mean(), "CONGU": congu.mean()}, axis=1)

        data = {}
        data["PG"] = pg
        data["PF"] = pf
        data["PF_DCLINE"] = pf_dcline
        data["LMP"] = lmp
        data["CONGL"] = congl
        data["CONGU"] = congu
        data["AVERAGED_CONG"] = average_cong
        data["LOAD_SHED"] = loadshed
        self._data = data

    def _get_data(self, key):
        return self._data[key]

    def get_grid(self):
        """Returns a transformed grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        return self.base_grid

    def get_profile(self, kind):
        """Returns demand, hydro, solar or wind  profile.

        :param str kind: either *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*pandas.DataFrame*) -- profile.
        """
        if kind == "demand":
            return self._demand.copy()
        elif kind == "hydro":
            return self._hydro.copy()
        elif kind == "solar":
            return self._solar.copy()
        elif kind == "wind":
            return self._wind.copy()
        else:
            raise ValueError(f"Unknown kind {kind}")

    def get_demand(self):
        """Returns demand profile.

        :return: (*pandas.DataFrame*) -- demand profile.
        """
        return self._demand

    get_base_grid = get_grid


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


def get_info_from_importable(obj):
    if is_pypsa_network(obj):
        return OrderedDict(
            [
                ("plan", ""),
                ("name", obj.name),
                ("id", -1),
                ("state", "analyze"),
                ("grid_model", ""),
                ("interconnect", ""),
                ("base_demand", ""),
                ("base_hydro", ""),
                ("base_solar", ""),
                ("base_wind", ""),
                ("change_table", ""),
                ("start_date", obj.snapshots[0]),
                ("end_date", obj.snapshots[-1]),
                ("interval", ""),
                ("engine", ""),
            ]
        )
    else:
        return OrderedDict()


def is_importable(obj):
    """
    Check whether powersimdata supports importing an object.
    """
    return is_pypsa_network(obj)  # and possibly others


def analyze_importable(obj):
    """
    Analyze an importable object.
    """
    assert is_importable(obj)

    if is_pypsa_network(obj):
        return AnalyzePypsa(obj)
    else:
        raise NotImplementedError(f"Analyze not implemented for this type {type(obj)}.")
