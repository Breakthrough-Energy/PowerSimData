import os
import pickle

import pandas as pd

from powersimdata.input.input_base import InputBase
from powersimdata.utility import server_setup


class InputData(InputBase):
    """Load input data."""

    def __init__(self):
        super().__init__()
        self._file_extension = {"ct": "pkl", "grid": "mat"}

    def _get_file_path(self, scenario_info, field_name):
        """Get the path to either grid or ct for the scenario

        :param dict scenario_info: metadata for a scenario.
        :param str field_name: either 'grid' or 'ct'
        :return: (*str*) -- the pyfilesystem path to the file
        """
        ext = self._file_extension[field_name]
        file_name = scenario_info["id"] + "_" + field_name + "." + ext
        return "/".join([*server_setup.INPUT_DIR, file_name])

    def _read(self, f, path):
        """Read data from file object

        :param io.IOBase f: an open file object
        :param str path: the path corresponding to f
        :raises ValueError: if extension is unknown.
        :return: (*dict* or *powersimdata.input.grid.Grid*) -- either a change table
            dict or grid object
        """
        ext = os.path.basename(path).split(".")[-1]
        if ext == "pkl":
            data = pd.read_pickle(f)
        elif ext == "mat":
            # get fully qualified local path to matfile
            data = os.path.abspath(path)
        else:
            raise ValueError("Unknown extension! %s" % ext)

        return data

    def save_change_table(self, ct, scenario_id):
        """Saves change table to the data store.

        :param dict ct: a change table
        :param str scenario_id: scenario id, used for file name
        """
        filepath = "/".join([*server_setup.INPUT_DIR, f"{scenario_id}_ct.pkl"])
        with self.data_access.write(filepath) as f:
            pickle.dump(ct, f)


def distribute_demand_from_zones_to_buses(zone_demand, bus):
    """Decomposes zone demand to bus demand based on bus 'Pd' column.

    :param pandas.DataFrame zone_demand: demand by zone. Index is timestamp, columns are
        zone IDs, values are zone demand (MW).
    :param pandas.DataFrame bus: table of bus data, containing at least 'zone_id' and
        'Pd' columns.
    :return: (*pandas.DataFrame*) -- data frame of demand. Index is timestamp, columns
        are bus IDs, values are bus demand (MW).
    :raises ValueError: if the columns of ``zone_demand`` don't match the set of zone
        IDs within the 'zone_id' column of ``bus``.
    """
    if set(bus["zone_id"].unique()) != set(zone_demand.columns):
        raise ValueError("zones don't match between zone_demand and bus dataframes")
    grouped_buses = bus.groupby("zone_id")
    bus_zone_pd = grouped_buses["Pd"].transform("sum")
    bus_zone_share = pd.concat(
        [pd.Series(bus["Pd"] / bus_zone_pd, name="zone_share"), bus["zone_id"]], axis=1
    )
    zone_bus_shares = bus_zone_share.pivot_table(
        index="bus_id",
        columns="zone_id",
        values="zone_share",
        dropna=False,
        fill_value=0,
    )
    bus_demand = zone_demand.dot(zone_bus_shares.T)

    return bus_demand
