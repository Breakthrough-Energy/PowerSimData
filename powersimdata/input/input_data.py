import os

import pandas as pd

from powersimdata.data_access.context import Context
from powersimdata.data_access.profile_helper import ProfileHelper
from powersimdata.utility import server_setup
from powersimdata.utility.helpers import MemoryCache, cache_key

_cache = MemoryCache()

profile_kind = {"demand", "hydro", "solar", "wind"}


_file_extension = {
    **{"ct": "pkl", "grid": "mat"},
    **{k: "csv" for k in profile_kind},
}


class InputHelper:
    def __init__(self, data_access):
        self.data_access = data_access

    @staticmethod
    def get_file_components(scenario_info, field_name):
        """Get the file name and relative path for either ct or grid.

        :param dict scenario_info: metadata for a scenario.
        :param str field_name: the input file type.
        :return: (*tuple*) -- file name and list of path components.
        """
        ext = _file_extension[field_name]
        file_name = scenario_info["id"] + "_" + field_name + "." + ext
        return file_name, server_setup.INPUT_DIR

    def download_file(self, file_name, from_dir):
        """Download the file if using server, otherwise no-op.

        :param str file_name: either grid or ct file name.
        :param tuple from_dir: tuple of path components.
        """
        from_dir = self.data_access.join(*from_dir)
        self.data_access.copy_from(file_name, from_dir)


def _check_field(field_name):
    """Checks field name.

    :param str field_name: *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
        *'ct'* or *'grid'*.
    :raises ValueError: if not *'demand'*, *'hydro'*, *'solar'*, *'wind'*
        *'ct'* or *'grid'*.
    """
    possible = list(_file_extension.keys())
    if field_name not in possible:
        raise ValueError("Only %s data can be loaded" % " | ".join(possible))


class InputData:
    """Load input data.

    :param str data_loc: data location.
    """

    def __init__(self, data_loc=None):
        """Constructor."""
        self.data_access = Context.get_data_access(data_loc)

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
        _check_field(field_name)
        print("--> Loading %s" % field_name)

        if field_name in profile_kind:
            helper = ProfileHelper
        else:
            helper = InputHelper(self.data_access)

        file_name, from_dir = helper.get_file_components(scenario_info, field_name)

        filepath = os.path.join(server_setup.LOCAL_DIR, *from_dir, file_name)
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
            helper.download_file(file_name, from_dir)
            data = _read_data(filepath)
        _cache.put(key, data)
        return data

    def get_profile_version(self, grid_model, kind):
        """Returns available raw profile from blob storage or local disk.

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*list*) -- available profile version.
        """
        return self.data_access.get_profile_version(grid_model, kind)

    def save_change_table(self, ct, scenario_id):
        """Saves change table to the data store.

        :param dict ct: a change table
        :param str scenario_id: scenario id, used for file name
        """

        # note pyfilesystem path conventions:
        # https://docs.pyfilesystem.org/en/latest/reference/path.html
        filepath = "/".join([*server_setup.INPUT_DIR, f"{scenario_id}_ct.pkl"])
        self.data_access.write(filepath, ct)


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


def get_bus_demand(scenario_info, grid):
    """Returns demand profiles by bus.

    :param dict scenario_info: scenario information.
    :param powersimdata.input.grid.Grid grid: grid to construct bus demand for.
    :return: (*pandas.DataFrame*) -- data frame of demand.
    """
    bus = grid.bus.copy()
    demand = InputData().get_data(scenario_info, "demand")[bus.zone_id.unique()]
    bus["zone_Pd"] = bus.groupby("zone_id")["Pd"].transform("sum")
    bus["zone_share"] = bus["Pd"] / bus["zone_Pd"]
    zone_bus_shares = pd.DataFrame(
        {z: bus.groupby("zone_id").get_group(z).zone_share for z in demand.columns}
    ).fillna(0)
    bus_demand = demand.dot(zone_bus_shares.T)

    return bus_demand
