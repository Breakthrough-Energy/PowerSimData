import pandas as pd
from fs import errors
from fs.multifs import MultiFS

from powersimdata.data_access.context import Context
from powersimdata.data_access.fs_helper import get_blob_fs
from powersimdata.input.input_base import InputBase
from powersimdata.utility import server_setup

profile_kind = {
    "demand",
    "hydro",
    "solar",
    "wind",
    "demand_flexibility_up",
    "demand_flexibility_dn",
    "demand_flexibility_cost_up",
    "demand_flexibility_cost_dn",
}


def get_profile_version(_fs, grid_model, kind):
    """Returns available raw profile from the given filesystem

    :param fs.base.FS _fs: filesystem instance
    :param str grid_model: grid model.
    :param str kind: *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
        *'demand_flexibility_up'*, *'demand_flexibility_dn'*,
        *'demand_flexibility_cost_up'*, or *'demand_flexibility_cost_dn'*.
    :return: (*list*) -- available profile version.
    """
    _fs = _fs.makedirs(f"raw/{grid_model}", recreate=True)
    matching = [f for f in _fs.listdir(".") if kind in f]

    # Don't include demand flexibility profiles as possible demand profiles
    if kind == "demand":
        matching = [p for p in matching if "demand_flexibility" not in p]
    return [f.replace(f"{kind}_", "").replace(".csv", "") for f in matching]


def _make_fs():
    mfs = MultiFS()
    writeable = server_setup.BLOB_TOKEN_RW is not None
    mfs.add_fs("profile_fs", get_blob_fs("profiles"), write=writeable)
    return mfs


class ProfileInput(InputBase):
    """Loads profile data"""

    def __init__(self):
        super().__init__()
        self._file_extension = {k: "csv" for k in profile_kind}
        self.data_access = Context.get_data_access(_make_fs)

    def _get_file_path(self, scenario_info, field_name):
        """Get the path to the specified profile

        :param dict scenario_info: metadata for a scenario.
        :param str field_name: the kind of profile.
        :return: (*str*) -- the pyfilesystem path to the file
        """
        if "demand_flexibility" in field_name:
            version = scenario_info[field_name]
        else:
            version = scenario_info["base_" + field_name]
        file_name = field_name + "_" + version + ".csv"
        grid_model = scenario_info["grid_model"]
        return "/".join(["raw", grid_model, file_name])

    def _read(self, f, path):
        """Read content from file object into data frame

        :param io.IOBase f: an open file object
        :param str path: the file path
        :return: (*pandas.DataFrame*) -- profile data frame
        """
        data = pd.read_csv(f, index_col=0, parse_dates=True)
        if "demand_flexibility" in path:
            data.columns = data.columns.astype(str)
        elif all(c.isdigit() for c in data.columns):
            data.columns = data.columns.astype(int)
        else:
            data.columns = data.columns.astype(str)
        return data

    def get_profile_version(self, grid_model, kind):
        """Returns available raw profile from blob storage or local disk.

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
            *'demand_flexibility_up'*, *'demand_flexibility_dn'*,
            *'demand_flexibility_cost_up'*, or *'demand_flexibility_cost_dn'*.
        :return: (*list*) -- available profile version.
        """

        def _callback(fs):
            return get_profile_version(fs, grid_model, kind)

        return self.data_access.get_profile_version(_callback)

    def upload(self, grid_model, name, profile):
        """Upload the given profile to blob storage and local cache

        :param str grid_model: the grid model
        :param str name: the file name for the profile, without extension
        :param pandas.DataFrame profile: profile data frame
        :raises ValueError: if no credential with write access is set
        """
        path = "/".join(["raw", grid_model, f"{name}.csv"])
        try:
            with self.data_access.write(path) as f:
                profile.to_csv(f)
        except errors.ResourceReadOnly:
            msg = (
                f"Profile {path} missing from blob storage and no credential with "
                f"write access provided. Please set the {server_setup.BLOB_KEY_NAME} "
                "environment variable to enable automatic upload."
            )
            raise ValueError(msg)
