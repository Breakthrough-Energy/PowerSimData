import warnings

import numpy as np
import pandas as pd

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.const import grid_const
from powersimdata.input.const.pypsa_const import pypsa_const
from powersimdata.network.constants.storage import storage as storage_const


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


def _get_storage_storagedata(n, storage_type):
    """Get storage data from PyPSA for data frame "StorageData" in PSD's
    storage dict.

    :param pypsa.Network n: PyPSA network to read in.
    :param str storage_type: key for PyPSA storage type.
    :return: (*pandas.DataFrame*) -- data frame with storage data.
    """
    if storage_type == "storage_units":
        storage_storagedata = _translate_df(n.storage_units, "storage_storagedata")

        p_nom = n.storage_units["p_nom"]
        e_nom = p_nom * n.storage_units["max_hours"]
        cyclic_state_of_charge = n.storage_units["cyclic_state_of_charge"]
        state_of_charge_initial = n.storage_units["state_of_charge_initial"]
    elif storage_type == "stores":
        storage_storagedata = _translate_df(n.stores, "storage_storagedata")

        e_nom = n.stores["e_nom"]
        cyclic_state_of_charge = n.stores["e_cyclic"]
        state_of_charge_initial = n.stores["e_initial"]

        # Efficiencies of Store are captured in link/dcline
        storage_storagedata["OutEff"] = 1
        storage_storagedata["InEff"] = 1
    else:
        warnings.warn(
            "Inapplicable storage_type passed to function _get_storage_storagedata."
        )

    # Initial storage: If cyclic, then fill half. If not cyclic, then apply PyPSA's state_of_charge_initial.
    storage_storagedata["InitialStorage"] = state_of_charge_initial.where(
        ~cyclic_state_of_charge, e_nom / 2
    )
    # Initial storage bounds: PSD's default is same as initial storage
    storage_storagedata["InitialStorageLowerBound"] = storage_storagedata[
        "InitialStorage"
    ]
    storage_storagedata["InitialStorageUpperBound"] = storage_storagedata[
        "InitialStorage"
    ]
    # Terminal storage bounds: If cyclic, then both same as initial storage. If not cyclic, then full capacity and zero.
    storage_storagedata["ExpectedTerminalStorageMax"] = e_nom * 1
    storage_storagedata["ExpectedTerminalStorageMin"] = e_nom * 0
    # Apply PSD's default relationships/assumptions for remaining columns
    storage_storagedata["InitialStorageCost"] = storage_const["energy_value"]
    storage_storagedata["TerminalStoragePrice"] = storage_const["energy_value"]
    storage_storagedata["MinStorageLevel"] = e_nom * storage_const["min_stor"]
    storage_storagedata["MaxStorageLevel"] = e_nom * storage_const["max_stor"]
    storage_storagedata["rho"] = 1

    return storage_storagedata


def _get_storage_gencost(n, storage_type):
    """Get storage data from PyPSA for data frame "gencost" in PSD's storage
    dict.

    :param pypsa.Network n: PyPSA network to read in.
    :param str storage_type: key for PyPSA storage type.
    :return: (*pandas.DataFrame*) -- data frame with storage data.
    """
    if storage_type == "storage_units":
        df_gencost = n.storage_units
    elif storage_type == "stores":
        df_gencost = n.stores
    else:
        warnings.warn(
            "Inapplicable storage_type passed to function _get_storage_gencost."
        )

    storage_gencost = _translate_df(df_gencost, "storage_gencost")
    storage_gencost.assign(type=2, n=3, c0=0, c2=0)

    return storage_gencost


def _get_storage_gen(n, storage_type):
    """Get storage data from PyPSA for data frame "gen" in PSD's storage dict.

    :param pypsa.Network n: PyPSA network to read in.
    :param str storage_type: key for PyPSA storage type.
    :return: (*pandas.DataFrame*) -- data frame with storage data.
    """
    if storage_type == "storage_units":
        df_gen = n.storage_units
        p_nom = n.storage_units["p_nom"]
    elif storage_type == "stores":
        df_gen = n.stores
        p_nom = np.inf
    else:
        warnings.warn("Inapplicable storage_type passed to function _get_storage_gen.")

    storage_gen = _translate_df(df_gen, "storage_gen")
    storage_gen["Pmax"] = +p_nom
    storage_gen["Pmin"] = -p_nom
    storage_gen["ramp_30"] = p_nom
    storage_gen["Vg"] = 1
    storage_gen["mBase"] = 100
    storage_gen["status"] = 1

    return storage_gen


class FromPyPSA(AbstractGrid):
    """Grid builder for PyPSA network object.

    :param pypsa.Network network: Network to read in.
    :param bool add_pypsa_cols: PyPSA data frames with renamed columns appended to
        Grid object data frames.
    """

    def __init__(self, network, add_pypsa_cols=True):
        """Constructor"""
        super().__init__()
        self._read_network(network, add_pypsa_cols=add_pypsa_cols)

    def _read_network(self, n, add_pypsa_cols=True):
        """PyPSA Network reader.

        :param pypsa.Network n: PyPSA network to read in.
        :param bool add_pypsa_cols: PyPSA data frames with renamed columns appended to
            Grid object data frames
        """

        # Interconnect and data location
        # only relevant if the PyPSA network was originally created from PSD
        interconnect = n.name.split(", ")
        if len(interconnect) > 1:
            data_loc = interconnect.pop(0)
        else:
            data_loc = "pypsa"

        # Read in data from PyPSA
        bus_in_pypsa = n.buses
        sub_in_pypsa = pd.DataFrame()
        bus2sub_in_pypsa = pd.DataFrame()
        gencost_cols = ["start_up_cost", "shut_down_cost", "marginal_cost"]
        gencost_in_pypsa = n.generators[gencost_cols]
        plant_in_pypsa = n.generators.drop(gencost_cols, axis=1)
        lines_in_pypsa = n.lines
        transformers_in_pypsa = n.transformers
        branch_in_pypsa = pd.concat(
            [lines_in_pypsa, transformers_in_pypsa],
            join="outer",
        )
        dcline_in_pypsa = n.links[lambda df: df.index.str[:3] != "sub"]
        storageunits_in_pypsa = n.storage_units
        stores_in_pypsa = n.stores

        # bus
        df = bus_in_pypsa.drop(columns="type")
        bus = _translate_df(df, "bus")
        bus.type.replace(["PQ", "PV", "Slack", ""], [1, 2, 3, 4], inplace=True)
        bus["bus_id"] = bus.index

        # zones mapping
        # only relevant if the PyPSA network was originally created from PSD
        if "zone_id" in n.buses and "zone_name" in n.buses:
            uniques = ~n.buses.zone_id.duplicated() * n.buses.zone_id.notnull()
            zone2id = (
                n.buses[uniques].set_index("zone_name").zone_id.astype(int).to_dict()
            )
            id2zone = _invert_dict(zone2id)
        else:
            zone2id = {}
            id2zone = {}

        # substations
        # only relevant if the PyPSA network was originally created from PSD
        if "is_substation" in bus:
            sub_cols = ["name", "interconnect_sub_id", "lat", "lon", "interconnect"]
            sub = bus[bus.is_substation][sub_cols]
            sub.index = sub[sub.index.str.startswith("sub")].index.str[3:]
            sub_in_pypsa_cols = [
                "name",
                "interconnect_sub_id",
                "y",
                "x",
                "interconnect",
            ]
            sub_in_pypsa = bus_in_pypsa[bus_in_pypsa.is_substation][sub_in_pypsa_cols]
            sub_in_pypsa.index = sub_in_pypsa[
                sub_in_pypsa.index.str.startswith("sub")
            ].index.str[3:]

            bus = bus[~bus.is_substation]
            bus_in_pypsa = bus_in_pypsa[~bus_in_pypsa.is_substation]

            bus2sub = bus[["substation", "interconnect"]].copy()
            bus2sub["sub_id"] = pd.to_numeric(
                bus2sub.pop("substation").str[3:], errors="ignore"
            )
            bus2sub_in_pypsa = bus_in_pypsa[["substation", "interconnect"]].copy()
            bus2sub_in_pypsa["sub_id"] = pd.to_numeric(
                bus2sub_in_pypsa.pop("substation").str[3:], errors="ignore"
            )
        else:
            warnings.warn("Substations could not be parsed.")
            sub = pd.DataFrame()
            bus2sub = pd.DataFrame()

        # shunts
        # append PyPSA's shunts information to PSD's buses data frame on columns
        if not n.shunt_impedances.empty:
            shunts = _translate_df(n.shunt_impedances, "bus")
            bus[["Bs", "Gs"]] = shunts[["Bs", "Gs"]]

        # plant
        df = plant_in_pypsa.drop(columns="type")
        plant = _translate_df(df, "generator")
        plant["ramp_30"] = n.generators["ramp_limit_up"].fillna(0)
        plant["Pmin"] *= plant["Pmax"]  # from relative to absolute value
        plant["bus_id"] = pd.to_numeric(plant.bus_id, errors="ignore")

        # generation costs
        # for type: type of cost model (1 piecewise linear, 2 polynomial), n: number of parameters for total cost function, c(0) to c(n-1): parameters
        gencost = _translate_df(gencost_in_pypsa, "gencost")
        gencost = gencost.assign(type=2, n=3, c0=0, c2=0)

        # branch
        # lines
        drop_cols = ["x", "r", "b", "g"]
        df = lines_in_pypsa.drop(columns=drop_cols, errors="ignore")
        lines = _translate_df(df, "branch")
        lines["branch_device_type"] = "Line"

        # transformers
        df = transformers_in_pypsa.drop(columns=drop_cols, errors="ignore")
        transformers = _translate_df(df, "branch")
        transformers["branch_device_type"] = "Transformer"

        branch = pd.concat([lines, transformers], join="outer")
        # BE model assumes a 100 MVA base, pypsa "assumes" a 1 MVA base
        branch["x"] *= 100
        branch["r"] *= 100
        branch["from_bus_id"] = pd.to_numeric(branch.from_bus_id, errors="ignore")
        branch["to_bus_id"] = pd.to_numeric(branch.to_bus_id, errors="ignore")

        # DC lines
        dcline = _translate_df(dcline_in_pypsa, "link")
        dcline["Pmin"] *= dcline["Pmax"]  # convert relative to absolute
        dcline["from_bus_id"] = pd.to_numeric(dcline.from_bus_id, errors="ignore")
        dcline["to_bus_id"] = pd.to_numeric(dcline.to_bus_id, errors="ignore")

        # storage
        storage_gen_storageunits = _get_storage_gen(n, "storage_units")
        storage_gencost_storageunits = _get_storage_gencost(n, "storage_units")
        storage_storagedata_storageunits = _get_storage_storagedata(n, "storage_units")
        storage_gen_stores = _get_storage_gen(n, "stores")
        storage_gencost_stores = _get_storage_gencost(n, "stores")
        storage_storagedata_stores = _get_storage_storagedata(n, "stores")

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
            (bus, bus_in_pypsa, grid_const.col_name_bus),
            (sub, sub_in_pypsa, grid_const.col_name_sub),
            (bus2sub, bus2sub_in_pypsa, grid_const.col_name_bus2sub),
            (plant, plant_in_pypsa, grid_const.col_name_plant),
            (gencost, gencost_in_pypsa, grid_const.col_name_gencost),
            (branch, branch_in_pypsa, grid_const.col_name_branch),
            (dcline, dcline_in_pypsa, grid_const.col_name_dcline),
            (
                storage_gen_storageunits,
                storageunits_in_pypsa,
                grid_const.col_name_plant,
            ),
            (
                storage_gencost_storageunits,
                storageunits_in_pypsa,
                grid_const.col_name_gencost,
            ),
            (
                storage_storagedata_storageunits,
                storageunits_in_pypsa,
                grid_const.col_name_storage_storagedata,
            ),
            (storage_gen_stores, stores_in_pypsa, grid_const.col_name_plant),
            (storage_gencost_stores, stores_in_pypsa, grid_const.col_name_gencost),
            (
                storage_storagedata_stores,
                stores_in_pypsa,
                grid_const.col_name_storage_storagedata,
            ),
        ]

        for k, v in zip(keys, values):
            df_psd, df_pypsa, const_location = v

            # Reindex
            if k == "branch":
                const_location += ["branch_device_type"]

            df_psd = df_psd.reindex(const_location, axis="columns")

            # Add renamed PyPSA columns
            if add_pypsa_cols:
                df_pypsa = df_pypsa.add_prefix("PyPSA_")

                df_psd = pd.concat([df_psd, df_pypsa], axis=1)

            # Convert to numeric
            df_psd.index = pd.to_numeric(df_psd.index, errors="ignore")

            data[k] = df_psd

        # Append individual columns
        if not n.shunt_impedances.empty:
            data["bus"]["includes_pypsa_shunt"] = True
        else:
            data["bus"]["includes_pypsa_shunt"] = False

        for df in (
            data["storage_gen_storageunits"],
            data["storage_gencost_storageunits"],
            data["storage_storagedata_storageunits"],
        ):
            df["which_storage_in_pypsa"] = "storage_units"

        for df in (
            data["storage_gen_stores"],
            data["storage_gencost_stores"],
            data["storage_storagedata_stores"],
        ):
            df["which_storage_in_pypsa"] = "stores"

        # Build PSD grid object
        self.data_loc = data_loc
        self.interconnect = interconnect
        self.bus = data["bus"]
        self.sub = data["sub"]
        self.bus2sub = data["bus2sub"]
        self.branch = data["branch"].sort_index()
        self.dcline = data["dcline"]
        self.zone2id = zone2id
        self.id2zone = id2zone
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
