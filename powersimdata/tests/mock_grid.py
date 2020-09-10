import pandas as pd

from powersimdata.input.grid import Grid

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
acceptable_keys = set(indices.keys()) | set(gencost_names.keys())

# The column names of each data frame attribute
sub_columns = ["name", "interconnect_sub_id", "lat", "lon", "interconnect"]

bus2sub_columns = ["sub_id", "interconnect"]

branch_columns = [
    "from_bus_id",
    "to_bus_id",
    "r",
    "x",
    "b",
    "rateA",
    "rateB",
    "rateC",
    "ratio",
    "angle",
    "status",
    "angmin",
    "angmax",
    "Pf",
    "Qf",
    "Pt",
    "Qt",
    "mu_Sf",
    "mu_St",
    "mu_angmin",
    "mu_angmax",
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

bus_columns = [
    "type",
    "Pd",
    "Qd",
    "Gs",
    "Bs",
    "zone_id",
    "Vm",
    "Va",
    "loss_zone",
    "baseKV",
    "Vmax",
    "Vmin",
    "lam_P",
    "lam_Q",
    "mu_Vmax",
    "mu_Vmin",
    "interconnect",
    "lat",
    "lon",
]

dcline_columns = [
    "from_bus_id",
    "to_bus_id",
    "status",
    "Pf",
    "Pt",
    "Qf",
    "Qt",
    "Vf",
    "Vt",
    "Pmin",
    "Pmax",
    "QminF",
    "QmaxF",
    "QminT",
    "QmaxT",
    "loss0",
    "loss1",
    "muPmin",
    "muPmax",
    "muQminF",
    "muQmaxF",
    "muQminT",
    "muQmaxT",
    "from_interconnect",
    "to_interconnect",
]

gencost_columns = ["type", "startup", "shutdown", "n", "c2", "c1", "c0", "interconnect"]

plant_columns = [
    "bus_id",
    "Pg",
    "Qg",
    "Qmax",
    "Qmin",
    "Vg",
    "mBase",
    "status",
    "Pmax",
    "Pmin",
    "Pc1",
    "Pc2",
    "Qc1min",
    "Qc1max",
    "Qc2min",
    "Qc2max",
    "ramp_agc",
    "ramp_10",
    "ramp_30",
    "ramp_q",
    "apf",
    "mu_Pmax",
    "mu_Pmin",
    "mu_Qmax",
    "mu_Qmin",
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


class MockGrid(object):
    def __init__(self, grid_attrs=None):
        """Constructor.

        :param dict grid_attrs: dictionary of {*field_name*, *data_dict*} pairs
            where *field_name* is the name of the data frame (sub, bus2sub,
            branch, bus, dcline, gencost or plant) and *data_dict* a dictionary
            in which the keys are the column name of the data frame associated
            to *field_name* and the values are a list of values.
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
        self.zone2id = {"zone1": 1, "zone2": 2}
        self.id2zone = {1: "zone1", 2: "zone2"}
        self.type2color = {}

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

    @property
    def __class__(self):
        """If anyone asks, I'm a Grid object!"""
        return Grid
