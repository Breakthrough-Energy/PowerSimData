import copy
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
        translators = self._revert_dict(pypsa_export_const[key]["rename_t"])
        df = pd.concat(
            {v: pnl[k].iloc[0] for k, v in translators.items() if k in pnl}, axis=1
        )
        return df

    def _revert_dict(self, d):
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


class _PypsaBuilder:
    """PyPSA Scenario Builder.

    :param str grid_model: grid model.
    :param list interconnect: list of interconnect(s) to build.
    :param pandas.DataFrame table: scenario list table
    """

    plan_name = ""
    scenario_name = ""
    # start_date = "2016-01-01 00:00:00"
    # end_date = "2016-12-31 23:00:00"
    # interval = "24H"
    demand = ""
    hydro = ""
    solar = ""
    wind = ""
    engine = "pypsa"
    exported_methods = {
        "set_base_profile",
        "set_engine",
        "set_name",
        "set_time",
        "get_ct",
        "get_grid",
        "get_base_grid",
        "get_demand",
        "get_hydro",
        "get_solar",
        "get_wind",
        "change_table",
    }

    def __init__(self, grid_model, interconnect, table):
        """Constructor."""
        # Circumvent cyclic imports
        from powersimdata.input.change_table import ChangeTable
        from powersimdata.input.grid import Grid

        if not is_pypsa_network(grid_model):
            raise TypeError(f"Expected a pypsa.Network, got {type(grid_model)}.")

        n = grid_model

        self.base_grid = Grid(n, source="pypsa")
        self.name = n.name
        self.interconnect = self.base_grid.interconnect
        self.grid_model = self.base_grid.grid_model
        self.change_table = ChangeTable(self.base_grid)
        self.existing = pd.Series(dtype=object)
        self.interconnect = self.base_grid.interconnect

        self.start_date = n.snapshots[0]
        self.end_date = n.snapshots[-1]
        self.interval = None

        from pypsa.descriptors import get_switchable_as_dense

        if not n.loads_t.p.empty:
            self._demand = n.loads_t.p.copy()
        else:
            self._demand = n.loads_t.p_set.copy()
        self._demand.columns = pd.to_numeric(self._demand.columns, errors="ignore")
        self._demand.columns.name = "bus_id"
        self._demand.index.name = "UTC Time"

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

    def get_ct(self):
        """Returns change table.

        :return: (*dict*) -- change table.
        """
        return copy.deepcopy(self.change_table.ct)

    def get_profile(self, kind):
        """Returns demand, hydro, solar or wind  profile.

        :param str kind: either *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*pandas.DataFrame*) -- profile.
        """
        if kind == "demand":
            return self._demand
        elif kind == "hydro":
            return self._hydro
        elif kind == "solar":
            return self._solar
        elif kind == "wind":
            return self._wind
        else:
            raise ValueError(f"Unknown kind {kind}")

    def get_demand(self):
        """Returns demand profile.

        :return: (*pandas.DataFrame*) -- data frame of demand (hour, zone id).
        """
        return self.get_profile("demand")

    def get_hydro(self):
        """Returns hydro profile.

        :return: (*pandas.DataFrame*) -- data frame of hydro power output (hour, plant).
        """
        return self.get_profile("hydro")

    def get_solar(self):
        """Returns solar profile.

        :return: (*pandas.DataFrame*) -- data frame of solar power output (hour, plant).
        """
        return self.get_profile("solar")

    def get_wind(self):
        """Returns wind profile.

        :return: (*pandas.DataFrame*) -- data frame of wind power output (hour, plant).
        """
        return self.get_profile("wind")

    def set_name(self, plan_name, scenario_name):
        """Sets scenario name.

        :param str plan_name: plan name
        :param str scenario_name: scenario name.
        :raises ValueError: if combination plan - scenario already exists
        """

        if plan_name in self.existing.plan.tolist():
            scenario = self.existing[self.existing.plan == plan_name]
            if scenario_name in scenario.name.tolist():
                raise ValueError(
                    "Combination %s - %s already exists" % (plan_name, scenario_name)
                )
        self.plan_name = plan_name
        self.scenario_name = scenario_name

    def set_time(self, start_date, end_date, interval):
        """Sets scenario start and end dates as well as the interval that will
        be used to split the date range.

        :param str start_date: start date.
        :param str end_date: start date.
        :param str interval: interval.
        :raises ValueError: if start date, end date or interval are invalid.
        """
        min_ts = pd.Timestamp("2016-01-01 00:00:00")
        max_ts = pd.Timestamp("2016-12-31 23:00:00")

        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        hours = (end_ts - start_ts) / np.timedelta64(1, "h") + 1
        if start_ts > end_ts:
            raise ValueError("start_date > end_date")
        elif start_ts < min_ts or start_ts >= max_ts:
            raise ValueError("start_date not in [%s,%s[" % (min_ts, max_ts))
        elif end_ts <= min_ts or end_ts > max_ts:
            raise ValueError("end_date not in ]%s,%s]" % (min_ts, max_ts))
        elif hours % int(interval.split("H", 1)[0]) != 0:
            raise ValueError("Incorrect interval for start and end dates")
        else:
            self.start_date = start_date
            self.end_date = end_date
            self.interval = interval

    def get_base_profile(self, kind):
        """Returns available base profiles.

        :param str kind: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*list*) -- available version for selected profile kind.
        """
        return [f"{self.start_date} - {self.end_date} from PyPSA network"]

    def set_base_profile(self, kind, version):
        raise NotImplementedError(
            "set_base_profile not implemented for models imported from PyPSA."
        )

    def set_engine(self, engine):
        """Sets simulation engine to be used for scenario.

        :param str engine: simulation engine
        """
        possible = ["pypsa"]
        if engine not in possible:
            print("Available engines: %s" % " | ".join(possible))
            return
        else:
            self.engine = engine

    def get_grid(self):
        """Returns a transformed grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        return self.base_grid

    def __str__(self):
        return self.name

    get_base_grid = get_grid
