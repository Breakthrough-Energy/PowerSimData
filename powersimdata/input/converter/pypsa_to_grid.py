import warnings

import numpy as np
import pandas as pd

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.const import grid_const
from powersimdata.input.const.pypsa_const import pypsa_const
from powersimdata.network.constants.carrier.storage import storage as storage_const


def _translate_df(df, key):
    """Rename columns of a data frame.

    :param pandas.DataFrame df: data frame to operate on.
    :param str key: key in :data:`powersimdata.input.const.pypsa_const.pypsa_const`
        dictionary.
    :return: (*pandas.DataFrame*) -- data frame with translated columns.
    """
    translators = _invert_dict(pypsa_const[key]["rename"])
    return df.rename(columns=translators)


def _invert_dict(d):
    """Revert dictionary

    :param dict d: dictionary to revert.
    :return: (*dict*) -- reverted dictionary.
    """
    return {v: k for k, v in d.items()}


def _get_storage_storagedata(df, storage_type):
    """Get storage data from PyPSA for data frame "StorageData" in PSD's
    storage dict.

    :param pandas.DataFrame df: PyPSA component dataframe.
    :param str storage_type: key for PyPSA storage type.
    :return: (*pandas.DataFrame*) -- data frame with storage data.
    """
    storage_storagedata = _translate_df(df, "storage_storagedata")

    if storage_type == "storage_units":

        e_nom = df.eval("p_nom * max_hours")
        state_of_charge_initial = df["state_of_charge_initial"]

    elif storage_type == "stores":

        e_nom = df["e_nom"]
        state_of_charge_initial = df["e_initial"]

        # Efficiencies of Store are captured in link/dcline
        storage_storagedata["OutEff"] = 1
        storage_storagedata["InEff"] = 1
    else:
        warnings.warn(
            "Inapplicable storage_type passed to function _get_storage_storagedata."
        )

    # Initial storage bounds: PSD's default is same as initial storage
    storage_storagedata["InitialStorageLowerBound"] = state_of_charge_initial
    storage_storagedata["InitialStorageUpperBound"] = state_of_charge_initial
    # Apply PSD's default relationships/assumptions for remaining columns
    storage_storagedata["InitialStorageCost"] = storage_const["energy_value"]
    storage_storagedata["TerminalStoragePrice"] = storage_const["energy_value"]
    storage_storagedata["rho"] = 1

    # fill with heuristic defaults if non-existent
    defaults = {
        "MinStorageLevel": e_nom * storage_const["min_stor"],
        "MaxStorageLevel": e_nom * storage_const["max_stor"],
        "ExpectedTerminalStorageMax": 1,
        "ExpectedTerminalStorageMin": 0,
    }
    for k, v in defaults.items():
        if k not in storage_storagedata:
            storage_storagedata[k] = v

    return storage_storagedata


def _get_storage_gencost(df, storage_type):
    """Get storage data from PyPSA for data frame "gencost" in PSD's storage
    dict.

    :param pandas.DataFrame df: PyPSA component dataframe.
    :param str storage_type: key for PyPSA storage type.
    :return: (*pandas.DataFrame*) -- data frame with storage data.
    """
    # There are "type" columns in gen and gencost with "type" column reserved
    # for gen dataframe, hence drop it here before renaming
    df = df.drop(columns="type", errors="ignore")
    storage_gencost = _translate_df(df, "storage_gencost")
    storage_gencost.assign(type=2, n=3, c0=0, c2=0)
    if "type" in storage_gencost:
        storage_gencost["type"] = pd.to_numeric(storage_gencost.type, errors="ignore")

    return storage_gencost


def _get_storage_gen(df, storage_type):
    """Get storage data from PyPSA for data frame "gen" in PSD's storage dict.

    :param pandas.DataFrame df: PyPSA component dataframe.
    :param str storage_type: key for PyPSA storage type.
    :return: (*pandas.DataFrame*) -- data frame with storage data.
    """
    if storage_type == "storage_units":
        pmax = df["p_nom"] * df["p_max_pu"]
        pmin = df["p_nom"] * df["p_min_pu"]
    elif storage_type == "stores":
        pmax = np.inf
        pmin = -np.inf
    else:
        warnings.warn("Inapplicable storage_type passed to function _get_storage_gen.")

    storage_gen = _translate_df(df, "storage_gen")
    storage_gen["Pmax"] = pmax
    storage_gen["Pmin"] = pmin
    storage_gen["ramp_30"] = pmax
    storage_gen["Vg"] = 1
    storage_gen["mBase"] = 100
    storage_gen["status"] = 1
    storage_gen["bus_id"] = pd.to_numeric(storage_gen.bus_id, errors="ignore")
    storage_gen["type"] = pd.to_numeric(storage_gen.type, errors="ignore")

    return storage_gen


class FromPyPSA(AbstractGrid):
    """Grid builder for PyPSA network object.

    :param pypsa.Network network: PyPSA network to read in.
    :param bool add_pypsa_cols: PyPSA data frames with renamed columns appended to
        Grid object data frames.
    """

    def __init__(self, network, add_pypsa_cols=True):
        """Constructor"""
        super().__init__()
        self.network = network
        self.add_pypsa_cols = add_pypsa_cols

    def _set_interconnect(self):
        if self.interconnect is None:
            self.interconnect = self.network.name.split(", ")

    def _set_data_loc(self):
        if len(self.interconnect) > 1:
            self.data_loc = self.interconnect[0]
        else:
            self.data_loc = "pypsa"

    def _set_zone_mapping(self):
        n = self.network
        if any(self.id2zone) and any(self.zone2id):
            return
        # only relevant if the PyPSA network was originally created from PSD
        if "zone_id" in n.buses and "zone_name" in n.buses:
            uniques = ~n.buses.zone_id.duplicated() * n.buses.zone_id.notnull()
            self.zone2id = (
                n.buses[uniques].set_index("zone_name").zone_id.astype(int).to_dict()
            )
            self.id2zone = _invert_dict(self.zone2id)

    def build(self):
        """PyPSA Network reader."""
        n = self.network
        add_pypsa_cols = self.add_pypsa_cols

        # Read in data from PyPSA
        bus_pypsa = n.buses
        sub_pypsa = pd.DataFrame()
        gencost_cols = ["start_up_cost", "shut_down_cost", "marginal_cost"]
        gencost_pypsa = n.generators[gencost_cols]
        plant_pypsa = n.generators.drop(gencost_cols, axis=1)
        lines_pypsa = n.lines
        transformers_pypsa = n.transformers
        branch_pypsa = pd.concat(
            [lines_pypsa, transformers_pypsa],
            join="outer",
        )
        dcline_pypsa = n.links[lambda df: df.index.str[:3] != "sub"]
        storageunits_pypsa = n.storage_units
        stores_pypsa = n.stores

        # bus
        df = bus_pypsa.drop(columns="type")
        bus = _translate_df(df, "bus")
        bus["type"] = bus.type.replace(
            ["(?i)PQ", "(?i)PV", "(?i)Slack", ""], [1, 2, 3, 4], regex=True
        ).astype(int)

        # substations
        # only relevant if the PyPSA network was originally created from PSD
        sub_cols = ["name", "interconnect_sub_id", "lat", "lon", "interconnect"]
        sub_pypsa_cols = [
            "y",
            "x",
        ]
        if "is_substation" in bus:
            sub = bus[bus.is_substation][sub_cols]
            sub.index = sub[sub.index.str.startswith("sub")].index.str[3:]
            sub_pypsa = bus_pypsa[bus_pypsa.is_substation][sub_pypsa_cols]
            sub_pypsa.index = sub.index

            bus = bus[~bus.is_substation]
            bus_pypsa = bus_pypsa[~bus_pypsa.is_substation]

            bus2sub = bus[["substation", "interconnect"]].copy()
            bus2sub["sub_id"] = pd.to_numeric(
                bus2sub.pop("substation").str[3:], errors="coerce"
            )
        else:
            # try to parse typical pypsa-eur(-sec) pattern for substations
            sub_pattern = "[A-Z][A-Z]\d+\s\d+$"

            sub = bus[bus.index.str.match(sub_pattern)].reindex(columns=sub_cols)
            sub["interconnect"] = np.nan
            sub["sub_id"] = sub.index
            sub_pypsa = bus_pypsa[bus_pypsa.index.str.match(sub_pattern)][
                sub_pypsa_cols
            ]

            sub_pattern = "([A-Z][A-Z]\d+\s\d+).*"
            bus2sub = pd.DataFrame(
                {
                    "sub_id": bus.index.str.extract(sub_pattern)[0].values,
                    "interconnect": np.nan,
                },
                index=bus.index,
            )

            if sub.empty and bus2sub.empty:
                warnings.warn("Substations could not be parsed.")
                sub = pd.DataFrame()
                bus2sub = pd.DataFrame()

        # shunts
        # append PyPSA's shunts information to PSD's buses data frame on columns
        if not n.shunt_impedances.empty:
            shunts = _translate_df(n.shunt_impedances, "bus")
            bus[["Bs", "Gs"]] = shunts[["Bs", "Gs"]]

        # plant
        df = plant_pypsa.drop(columns="type")
        plant = _translate_df(df, "generator")
        plant["ramp_30"] = n.generators["ramp_limit_up"].fillna(0)
        plant["Pmin"] *= plant["Pmax"]  # from relative to absolute value
        plant["lat"] = plant.bus_id.map(bus.lat)
        plant["lon"] = plant.bus_id.map(bus.lon)
        plant["bus_id"] = pd.to_numeric(plant.bus_id, errors="ignore")

        # generation costs
        # for type: type of cost model (1 piecewise linear, 2 polynomial), n: number of parameters for total cost function, c(0) to c(n-1): parameters
        gencost = _translate_df(gencost_pypsa, "gencost")
        gencost = gencost.assign(
            type=2, n=3, c0=0, c2=0, interconnect=plant.get("interconnect")
        )

        # branch
        # lines
        drop_cols = ["x", "r", "b", "g"]
        df = lines_pypsa.drop(columns=drop_cols, errors="ignore")
        lines = _translate_df(df, "branch")
        lines["branch_device_type"] = lines.get("branch_device_type", "Line")

        # transformers
        df = transformers_pypsa.drop(columns=drop_cols, errors="ignore")
        transformers = _translate_df(df, "branch")
        transformers["branch_device_type"] = transformers.get(
            "branch_device_type", "Transformer"
        )

        branch = pd.concat([lines, transformers], join="outer")
        # BE model assumes a 100 MVA base, pypsa "assumes" a 1 MVA base
        branch["x"] *= 100
        branch["r"] *= 100
        branch["from_lat"] = branch.from_bus_id.map(bus.lat)
        branch["from_lon"] = branch.from_bus_id.map(bus.lon)
        branch["to_lat"] = branch.to_bus_id.map(bus.lat)
        branch["to_lon"] = branch.to_bus_id.map(bus.lon)
        branch["from_bus_id"] = pd.to_numeric(branch.from_bus_id, errors="ignore")
        branch["to_bus_id"] = pd.to_numeric(branch.to_bus_id, errors="ignore")

        # DC lines
        dcline = _translate_df(dcline_pypsa, "link")
        dcline["Pmin"] *= dcline["Pmax"]  # convert relative to absolute
        dcline["from_bus_id"] = pd.to_numeric(dcline.from_bus_id, errors="ignore")
        dcline["to_bus_id"] = pd.to_numeric(dcline.to_bus_id, errors="ignore")

        # storage units
        c = "storage_units"
        storage_gen_storageunits = _get_storage_gen(n.storage_units, c)
        storage_gencost_storageunits = _get_storage_gencost(n.storage_units, c)
        storage_storagedata_storageunits = _get_storage_storagedata(n.storage_units, c)

        inflow = n.get_switchable_as_dense("StorageUnit", "inflow")
        has_inflow = inflow.any()
        if has_inflow.any():
            # add artificial buses
            suffix = " inflow"

            def add_suffix(s):
                return str(s) + suffix

            storage_gen_inflow = storage_gen_storageunits[has_inflow]
            buses_old = storage_gen_inflow.bus_id.astype(str)
            buses_new = storage_gen_inflow.index
            bus_rename = dict(zip(buses_old, buses_new))
            bus_inflow = bus.reindex(buses_old).rename(index=bus_rename)
            bus2sub_inflow = bus2sub.reindex(buses_old).rename(index=bus_rename)

            # add discharging dcline (has same index as inflow storages)
            dcline_inflow = pd.DataFrame(
                {
                    "from_bus_id": buses_new,
                    "to_bus_id": buses_old,
                    "Pmax": storage_gen_inflow.Pmax,
                    "Pmin": storage_gen_inflow.Pmin,
                }
            )

            # add inflow generator
            gen_inflow = storage_gen_inflow.rename(index=add_suffix)
            gen_inflow["bus_id"] = buses_new
            gen_inflow["Pmax"] = n.storage_units_t.inflow.max().rename(add_suffix)
            gen_inflow["capital_cost"] = 0.0
            gen_inflow["p_nom_extendable"] = False
            gen_inflow["committable"] = False
            gen_inflow["type"] = "inflow"
            gen_inflow["lat"] = gen_inflow.bus_id.map(bus.lat)
            gen_inflow["lon"] = gen_inflow.bus_id.map(bus.lon)
            gen_inflow = gen_inflow.reindex(columns=plant.columns)
            gencost_inflow = storage_gencost_storageunits[has_inflow].rename(
                index=add_suffix
            )
            gencost_inflow = storage_gencost_storageunits.assign(
                c0=0, c1=0, c2=0, type=2, startup=0, shutdown=0, n=3
            )

            # add everything to data
            storage_gen_storageunits.loc[has_inflow, "bus_id"] = buses_new
            storage_gen_storageunits.loc[
                has_inflow, "Pmin"
            ] = -np.inf  # don't limit charging from inflow
            bus = pd.concat([bus, bus_inflow])
            bus2sub = pd.concat([bus2sub, bus2sub_inflow])
            plant = pd.concat([plant, gen_inflow])
            gencost = pd.concat([gencost, gencost_inflow])
            dcline = pd.concat([dcline, dcline_inflow])

        # stores
        c = "stores"
        storage_gen_stores = _get_storage_gen(n.stores, c)
        storage_gencost_stores = _get_storage_gencost(n.stores, c)
        storage_storagedata_stores = _get_storage_storagedata(n.stores, c)
        storage_genfuel = list(n.storage_units.carrier) + list(n.stores.carrier)

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

        # Reindex data and add PyPSA columns
        data = dict()
        keys = [
            "bus",
            "sub",
            "bus2sub",
            "plant",
            "gencost",
            "branch",
            "dcline",
            "storage_gen_storageunits",
            "storage_gencost_storageunits",
            "storage_storagedata_storageunits",
            "storage_gen_stores",
            "storage_gencost_stores",
            "storage_storagedata_stores",
        ]
        values = [
            (bus, bus_pypsa, grid_const.col_name_bus),
            (sub, sub_pypsa, grid_const.col_name_sub),
            (bus2sub, None, grid_const.col_name_bus2sub),
            (plant, plant_pypsa, grid_const.col_name_plant),
            (gencost, gencost_pypsa, grid_const.col_name_gencost),
            (branch, branch_pypsa, grid_const.col_name_branch),
            (dcline, dcline_pypsa, grid_const.col_name_dcline),
            (
                storage_gen_storageunits,
                storageunits_pypsa,
                grid_const.col_name_plant,
            ),
            (
                storage_gencost_storageunits,
                storageunits_pypsa,
                grid_const.col_name_gencost,
            ),
            (
                storage_storagedata_storageunits,
                storageunits_pypsa,
                grid_const.col_name_storage_storagedata,
            ),
            (storage_gen_stores, stores_pypsa, grid_const.col_name_plant),
            (storage_gencost_stores, stores_pypsa, grid_const.col_name_gencost),
            (
                storage_storagedata_stores,
                stores_pypsa,
                grid_const.col_name_storage_storagedata,
            ),
        ]

        for k, v in zip(keys, values):
            df_psd, df_pypsa, const_location = v

            df_psd = df_psd.reindex(const_location, axis="columns")

            # Add renamed PyPSA columns
            if add_pypsa_cols and df_pypsa is not None:
                df_pypsa = df_pypsa.add_prefix("pypsa_")

                df_psd = pd.concat([df_psd, df_pypsa], axis=1)

            # Convert to numeric
            df_psd.index = pd.to_numeric(df_psd.index, errors="ignore")

            data[k] = df_psd

        for df in (
            data["storage_gen_storageunits"],
            data["storage_gencost_storageunits"],
            data["storage_storagedata_storageunits"],
        ):
            df["pypsa_component"] = "storage_units"

        for df in (
            data["storage_gen_stores"],
            data["storage_gencost_stores"],
            data["storage_storagedata_stores"],
        ):
            df["pypsa_component"] = "stores"

        # Build PSD grid object

        # Interconnect and data location
        # only relevant if the PyPSA network was originally created from PSD
        self._set_interconnect()
        self._set_data_loc()
        self._set_zone_mapping()

        self.bus = data["bus"]
        self.sub = data["sub"]
        self.bus2sub = data["bus2sub"]
        self.branch = data["branch"].sort_index()
        self.dcline = data["dcline"]
        self.plant = data["plant"]
        self.gencost["before"] = data["gencost"]
        self.gencost["after"] = data["gencost"]
        self.storage["gen"] = pd.concat(
            [data["storage_gen_storageunits"], data["storage_gen_stores"]],
            join="outer",
        )
        self.storage["gencost"] = pd.concat(
            [data["storage_gencost_storageunits"], data["storage_gencost_stores"]],
            join="outer",
        )
        self.storage["StorageData"] = pd.concat(
            [
                data["storage_storagedata_storageunits"],
                data["storage_storagedata_stores"],
            ],
            join="outer",
        )
        self.storage["genfuel"] = storage_genfuel
        self.storage.update(storage_const)

        # Set index names to match PSD
        self.bus.index.name = "bus_id"
        self.plant.index.name = "plant_id"
        self.gencost["before"].index.name = "plant_id"
        self.gencost["after"].index.name = "plant_id"
        self.branch.index.name = "branch_id"
        self.dcline.index.name = "dcline_id"
        self.sub.index.name = "sub_id"
        self.bus2sub.index.name = "bus_id"
        self.storage["gen"].index.name = "storage_id"
        self.storage["gencost"].index.name = "storage_id"
        self.storage["StorageData"].index.name = "storage_id"
        return self

    def _translate_pnl(self, pnl, key):
        """Translate time-dependent data frames with one time step from PyPSA to static
        data frames.

        :param str pnl: name of the time-dependent dataframe.
        :param str key: key in :data:`powersimdata.input.const.pypsa_const.pypsa_const`
            dictionary.
        :return: (*pandas.DataFrame*) -- the static data frame.
        """
        translators = _invert_dict(pypsa_const[key]["rename_t"])
        df = pd.concat(
            {v: pnl[k].iloc[0] for k, v in translators.items() if k in pnl}, axis=1
        )
        return df
