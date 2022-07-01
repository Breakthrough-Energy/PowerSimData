import warnings

import numpy as np
import pandas as pd

from powersimdata.input.abstract_grid import AbstractGrid, storage_template
from powersimdata.input.exporter.export_to_pypsa import (
    pypsa_const as pypsa_export_const,
)
from powersimdata.network.constants.storage import storage as storage_const

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
        "drop_cols_in_advance": [
            "type"
        ],
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
        # these need to be dropped as they appear in both pypsa and powersimdata
        # but need to be translated at the same time
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
    "storage_gen": {
        "default_drop_cols": [
            "Qmax",
            "Qmin",
            "Pc1",
            "Pc2",
            "Qc1min",
            "Qc1max",
            "Qc2min",
            "Qc2max",
            "ramp_agc",
            "ramp_10",
            "ramp_q",
            "apf",
            "mu_Pmax",
            "mu_Pmin",
            "mu_Qmax",
            "mu_Qmin",
        ]
    },
    "storage_gencost": {
        "drop_cols_in_advance": [
            "type"
        ],
        "default_drop_cols": [
            "startup",
            "shutdown",
            "c2",
            "c0",
        ]
    },
    "storage_StorageData": {
        "default_select_cols": [
            "UnitIdx",
        ]
    },
}


class FromPyPSA(AbstractGrid):
    """Grid builder for PyPSA network object.

    :param pypsa.Network network: Network to read in.
    :param bool drop_cols: columns to be dropped off PyPSA data frames
    """

    def __init__(self, network, drop_cols=True):
        """Constructor"""
        super().__init__()
        self._read_network(network, drop_cols=drop_cols)

    def _read_network(self, n, drop_cols=True):
        """PyPSA Network reader.

        :param pypsa.Network network: Network to read in.
        :param bool drop_cols: columns to be dropped off PyPSA data frames
        """

        # Interconnect and data location
        # relevant if the PyPSA network was originally created from powersimdata
        interconnect = n.name.split(", ")
        if len(interconnect) > 1:
            data_loc = interconnect.pop(0)
        else:
            data_loc = "pypsa"

        # bus
        df = n.df("Bus").drop(columns="type")
        bus = self._translate_df(df, "bus")
        bus["type"] = bus.type.replace(["PQ", "PV", "slack", ""], [1, 2, 3, 4])
        bus.index.name = "bus_id"

        # zones mapping
        # non-empty if the PyPSA network was originally created from powersimdata
        if "zone_id" in n.buses and "zone_name" in n.buses:
            uniques = ~n.buses.zone_id.duplicated() * n.buses.zone_id.notnull()
            zone2id = (
                n.buses[uniques].set_index("zone_name").zone_id.astype(int).to_dict()
            )
            id2zone = self._invert_dict(zone2id)
        else:
            zone2id = {}
            id2zone = {}

        # substations
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

        # shunts
        if not n.shunt_impedances.empty:
            shunts = self._translate_df(n.shunt_impedances, "bus")
            bus[["Bs", "Gs"]] = shunts[["Bs", "Gs"]]

        # plant
        drop_cols = pypsa_import_const["generator"]["drop_cols_in_advance"]
        df = n.generators.drop(columns=drop_cols)
        plant = self._translate_df(df, "generator")
        plant["ramp_30"] = n.generators["ramp_limit_up"].fillna(0)
        plant["Pmin"] *= plant["Pmax"]  # from relative to absolute value
        plant["bus_id"] = pd.to_numeric(plant.bus_id, errors="ignore")
        plant.index.name = "plant_id"

        # generation costs
        cols = pypsa_import_const["gencost"]["default_select_cols"]
        gencost = self._translate_df(df, "cost")
        gencost = gencost.assign(type=2, n=3, c0=0, c2=0)
        gencost = gencost.reindex(columns=cols)
        gencost.index.name = "plant_id"

        # branch
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

        # DC lines
        df = n.df("Link")[lambda df: df.index.str[:3] != "sub"]
        dcline = self._translate_df(df, "link")
        dcline["Pmin"] *= dcline["Pmax"]  # convert relative to absolute
        dcline["from_bus_id"] = pd.to_numeric(dcline.from_bus_id, errors="ignore")
        dcline["to_bus_id"] = pd.to_numeric(dcline.to_bus_id, errors="ignore")

        # storages
        drop_cols_gencost = pypsa_import_const["storage_gencost"]["drop_cols_in_advance"]
        df_gen = n.storage_units
        df_gencost = n.storage_units.drop(columns=drop_cols_gencost)
        df_StorageData = n.storage_units

        # rename columns that can be directly imported from pypsa to grid, based on dict from pypsa_export_const
        storage_gen = self._translate_df(df_gen, "storage_gen")
        storage_gencost = self._translate_df(df_gencost, "storage_gencost")
        storage_StorageData = self._translate_df(df_StorageData, "storage_StorageData")

        # Powersimdata's default relationships between variables taken from function "_add_storage_data" in transform_grid.py

        # Frequently used PyPSA variables
        p_nom = n.storage_units['p_nom']
        max_hours = n.storage_units['max_hours']
        cyclic_state_of_charge = n.storage_units['cyclic_state_of_charge']
        state_of_charge_initial = n.storage_units['state_of_charge_initial']

        # Individual column adjustments for storage_gen
        storage_gen['Pmax'] = + p_nom
        storage_gen['Pmin'] = - p_nom
        storage_gen['ramp_30'] = p_nom
        storage_gen['Vg'] = 1
        storage_gen['mBase'] = 100
        storage_gen['status'] = 1

        # Individual column adjustments for storage_gencost            
        storage_gencost['type'] = 2
        storage_gencost['n'] = 3

        # Individual column adjustments for storage_StorageData
        # Initial storage: If cyclic, then fill half. If not cyclic, then apply PyPSA's state_of_charge_initial.
        storage_StorageData['InitialStorage'] = state_of_charge_initial.where(~cyclic_state_of_charge,max_hours * p_nom / 2)
        # Initial storage bounds: Powersimdata's default is same as initial storage
        storage_StorageData['InitialStorageLowerBound'] = storage_StorageData['InitialStorage']
        storage_StorageData['InitialStorageUpperBound'] = storage_StorageData['InitialStorage']
        # Terminal storage bounds: If cyclic, then both same as initial storage. If not cyclic, then full capacity and zero.
        storage_StorageData['ExpectedTerminalStorageMax'] = max_hours * p_nom * 1
        storage_StorageData['ExpectedTerminalStorageMin'] = max_hours * p_nom * 0
        # Apply powersimdata's default relationships/assumptions for remaining columns
        storage_StorageData['InitialStorageCost'] = storage_const['energy_value']
        storage_StorageData['TerminalStoragePrice'] = storage_const['energy_value']
        storage_StorageData['MinStorageLevel'] = p_nom * max_hours * storage_const['min_stor']
        storage_StorageData['MaxStorageLevel'] = p_nom * max_hours * storage_const['max_stor']
        storage_StorageData['rho'] = 1

        storage_gen.index.name = "storage_id"
        storage_gencost.index.name = "storage_id"
        storage_StorageData.index.name = "storage_id"

        # Drop columns if wanted
        if drop_cols:
            self._drop_cols(bus, "bus")
            self._drop_cols(plant, "generator")
            self._drop_cols(branch, "branch")
            self._drop_cols(dcline, "link")
            self._drop_cols(storage_gen, "storage_gen")
            self._drop_cols(storage_gencost, "storage_gencost")
                         
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
        for df in (bus, sub, bus2sub, gencost, plant, branch, dcline, storage_gen, storage_gencost, storage_StorageData):
            df.index = pd.to_numeric(df.index, errors="ignore")

        # Pull together storage dictionary
        storage = storage_template()
        storage["gen"] = storage_gen
        storage["gencost"] = storage_gencost
        storage["StorageData"] = storage_StorageData            

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
        self.storage = storage

    def _drop_cols(self, df, key):
        """Drop columns in data frame. Done inplace.

        :param pandas.DataFrame df: data frame to operate on.
        :param str key: key in the :data:`pypsa_import_const` dictionary.
        """
        cols = pypsa_import_const[key]["default_drop_cols"]
        df.drop(columns=cols, inplace=True, errors="ignore")

    def _translate_df(self, df, key):
        """Rename columns of a data frame.

        :param pandas.DataFrame df: data frame to operate on.
        :param str key: key in the :data:`pypsa_import_const` dictionary.
        """
        translators = self._invert_dict(pypsa_export_const[key]["rename"])
        return df.rename(columns=translators)

    def _translate_pnl(self, pnl, key):
        """Translate time-dependent data frames with one time step from pypsa to static
        data frames.

        :param str pnl: name of the time-dependent dataframe.
        :param str key: key in the :data:`pypsa_import_const` dictionary.
        :return: (*pandas.DataFrame*) -- the static data frame
        """
        translators = self._invert_dict(pypsa_export_const[key]["rename_t"])
        df = pd.concat(
            {v: pnl[k].iloc[0] for k, v in translators.items() if k in pnl}, axis=1
        )
        return df

    def _invert_dict(self, d):
        """Revert dictionary

        :param dict d: dictionary to revert.
        :return: (*dict*) -- reverted dictionary.
        """
        return {v: k for k, v in d.items()}
