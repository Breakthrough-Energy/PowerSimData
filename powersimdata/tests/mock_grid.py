import pandas as pd

from powersimdata.input import const
from powersimdata.input.grid import Grid
from powersimdata.network.model import ModelImmutables

# The index name of each data frame attribute
indices = {
    "sub": "sub_id",
    "bus2sub": "bus_id",
    "branch": "branch_id",
    "bus": "bus_id",
    "dcline": "dcline_id",
    "plant": "plant_id",
}

gencost_names = {"gencost_before": "before", "gencost_after": "after"}
storage_names = {"storage_gen": "gen", "storage_StorageData": "StorageData"}
acceptable_keys = (
    set(indices.keys()) | set(gencost_names.keys()) | set(storage_names.keys())
)

# The column names of each data frame attribute
sub_columns = ["name", "interconnect_sub_id", "lat", "lon", "interconnect"]

bus2sub_columns = ["sub_id", "interconnect"]

branch_augment_columns = [
    "branch_device_type",
    "interconnect",
    "from_zone_id",
    "to_zone_id",
    "from_zone_name",
    "to_zone_name",
    "from_lat",
    "from_lon",
    "to_lat",
    "to_lon",
]
branch_columns = const.col_name_branch + branch_augment_columns

bus_augment_columns = ["interconnect", "lat", "lon"]
bus_columns = const.col_name_bus + bus_augment_columns

dcline_augment_columns = ["from_interconnect", "to_interconnect"]
dcline_columns = const.col_name_dcline + dcline_augment_columns

gencost_augment_columns = ["interconnect"]
gencost_columns = const.col_name_gencost + gencost_augment_columns

plant_augment_columns = [
    "type",
    "interconnect",
    "GenFuelCost",
    "GenIOB",
    "GenIOC",
    "GenIOD",
    "zone_id",
    "zone_name",
    "lat",
    "lon",
]
plant_columns = const.col_name_plant + plant_augment_columns

storage_columns = {
    # The first 21 columns of plant are all that's necessary
    "gen": plant_columns[:21],
    "StorageData": const.col_name_storage_storagedata,
}


class MockGrid:
    def __init__(self, grid_attrs=None, model="usa_tamu"):
        """Constructor.

        :param dict grid_attrs: dictionary of {*field_name*, *data_dict*} pairs
            where *field_name* is the name of the data frame (sub, bus2sub,
            branch, bus, dcline, gencost or plant) and *data_dict* a dictionary
            in which the keys are the column name of the data frame associated
            to *field_name* and the values are a list of values.
        :param str model: grid model. Use to access geographical information such
            as loadzones, interconnections, etc.
        """
        if grid_attrs is None:
            grid_attrs = {}

        if not isinstance(grid_attrs, dict):
            raise TypeError("grid_attrs must be a dict")

        for key in grid_attrs.keys():
            if not isinstance(key, str):
                raise TypeError("grid_attrs keys must all be str")

        extra_keys = set(grid_attrs.keys()) - acceptable_keys
        if len(extra_keys) > 0:
            raise ValueError("Got unknown key(s):" + str(extra_keys))

        self.grid_model = model
        self.model_immutables = ModelImmutables(model)

        cols = {
            "sub": sub_columns,
            "bus2sub": bus2sub_columns,
            "branch": branch_columns,
            "bus": bus_columns,
            "dcline": dcline_columns,
            "plant": plant_columns,
        }

        self.data_loc = None
        self.interconnect = None
        self.zone2id = {}
        self.id2zone = {}

        # Loop through names for grid data frames, add (maybe empty) data
        # frames.
        for df_name in indices:
            if df_name in grid_attrs:
                df = pd.DataFrame(grid_attrs[df_name])
            else:
                df = pd.DataFrame(columns=([indices[df_name]] + cols[df_name]))
            df.set_index(indices[df_name], inplace=True)
            setattr(self, df_name, df)

        # Gencost is special because there are two dataframes in a dict
        gencost = {}
        for gridattr_name, gc_name in gencost_names.items():
            if gridattr_name in grid_attrs:
                df = pd.DataFrame(grid_attrs[gridattr_name])
            else:
                df = pd.DataFrame(columns=(["plant_id"] + gencost_columns))
            df.set_index("plant_id", inplace=True)
            gencost[gc_name] = df
        self.gencost = gencost

        # Storage is special because there are multiple dataframes in a dict
        storage = {}
        for storage_attr_name, storage_name in storage_names.items():
            if storage_attr_name in grid_attrs:
                df = pd.DataFrame(grid_attrs[storage_attr_name])
            else:
                df = pd.DataFrame(
                    columns=(["plant_id"] + storage_columns[storage_name])
                )
            storage[storage_name] = df
        self.storage = storage

    @property
    def __class__(self):
        """If anyone asks, I'm a Grid object!"""
        return Grid
