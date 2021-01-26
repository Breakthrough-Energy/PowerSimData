import os
import posixpath

import pandas as pd

from powersimdata.data_access.context import Context
from powersimdata.utility import server_setup
from powersimdata.utility.helpers import MemoryCache, cache_key

_cache = MemoryCache()


class InputData(object):
    """Load input data.

    :param str data_loc: data location.
    """

    def __init__(self, data_loc=None):
        """Constructor."""
        os.makedirs(server_setup.LOCAL_DIR, exist_ok=True)

        self.file_extension = {
            "demand": "csv",
            "hydro": "csv",
            "solar": "csv",
            "wind": "csv",
            "ct": "pkl",
            "grid": "mat",
        }
        self.data_access = Context.get_data_access(data_loc)

    def _check_field(self, field_name):
        """Checks field name.

        :param str field_name: *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
            *'ct'* or *'grid'*.
        :raises ValueError: if not *'demand'*, *'hydro'*, *'solar'*, *'wind'*
            *'ct'* or *'grid'*
        """
        possible = list(self.file_extension.keys())
        if field_name not in possible:
            raise ValueError("Only %s data can be loaded" % " | ".join(possible))

    def get_data(self, scenario_info, field_name):
        """Returns data either from server or local directory.

        :param dict scenario_info: scenario information.
        :param str field_name: *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
            *'ct'* or *'grid'*.
        :return: (*pandas.DataFrame*, *dict*, or *str*) --
            demand, hydro, solar or wind as a data frame, change table as a
            dictionary, or the path to a matfile enclosing the grid data.
        :raises FileNotFoundError: if file not found on local machine.
        """
        self._check_field(field_name)

        print("--> Loading %s" % field_name)
        ext = self.file_extension[field_name]

        if field_name in ["demand", "hydro", "solar", "wind"]:
            version = scenario_info["base_" + field_name]
            file_name = field_name + "_" + version + "." + ext
            from_dir = posixpath.join(
                server_setup.BASE_PROFILE_DIR, scenario_info["grid_model"]
            )
        else:
            file_name = scenario_info["id"] + "_" + field_name + "." + ext
            from_dir = server_setup.INPUT_DIR

        filepath = os.path.join(server_setup.LOCAL_DIR, from_dir, file_name)
        key = cache_key(filepath)
        cached = _cache.get(key)
        if cached is not None:
            return cached
        try:
            data = _read_data(filepath)
        except FileNotFoundError:
            print(
                "%s not found in %s on local machine"
                % (file_name, server_setup.LOCAL_DIR)
            )
            self.data_access.copy_from(file_name, from_dir)
            data = _read_data(filepath)
        _cache.put(key, data)
        return data


def _read_data(filepath):
    """Reads data from local machine.

    :param str filepath: path to file, with extension either 'pkl', 'csv', or 'mat'.
    :return: (*pandas.DataFrame*, *dict*, or *str*) -- demand, hydro, solar or
        wind as a data frame, change table as a dict, or str containing a
        local path to a matfile of grid data.
    :raises ValueError: if extension is unknown.
    """
    ext = os.path.basename(filepath).split(".")[-1]
    if ext == "pkl":
        data = pd.read_pickle(filepath)
    elif ext == "csv":
        data = pd.read_csv(filepath, index_col=0, parse_dates=True)
        data.columns = data.columns.astype(int)
    elif ext == "mat":
        # Try to load the matfile, just to check if it exists locally
        open(filepath, "r")
        data = filepath
    else:
        raise ValueError("Unknown extension! %s" % ext)

    return data


def get_bus_demand(scenario_id, grid):
    """Returns demand profiles by bus.

    :param str scenario_id: scenario id.
    :param powersimdata.input.grid.Grid grid: grid to construct bus demand for.
    :return: (*pandas.DataFrame*) -- data frame of demand.
    """
    demand = InputData().get_data(scenario_id, "demand")
    bus = grid.bus
    bus["zone_Pd"] = bus.groupby("zone_id")["Pd"].transform("sum")
    bus["zone_share"] = bus["Pd"] / bus["zone_Pd"]
    zone_bus_shares = pd.DataFrame(
        {z: bus.groupby("zone_id").get_group(z).zone_share for z in demand.columns}
    ).fillna(0)
    bus_demand = demand.dot(zone_bus_shares.T)

    return bus_demand
