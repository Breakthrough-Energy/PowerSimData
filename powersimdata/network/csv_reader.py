import os

import pandas as pd


class CSVReader:
    """Read CSV files enclosing a grid model.

    :param str data_loc: path to data.
    """

    def __init__(self, data_loc):
        """Constructor"""
        self.bus = read(data_loc, "bus.csv")
        self.plant = read(data_loc, "plant.csv")
        self.gencost = read(data_loc, "gencost.csv")
        self.branch = read(data_loc, "branch.csv")
        self.dcline = read(data_loc, "dcline.csv")
        self.sub = read(data_loc, "sub.csv")
        self.bus2sub = read(data_loc, "bus2sub.csv")
        self.zone = read(data_loc, "zone.csv")


def read(data_loc, filename):
    """Reads CSV.

    :return: (*pandas.DataFrame*) -- created data frame.
    """
    path = os.path.join(data_loc, filename)
    if os.path.isfile(path):
        print("Reading %s" % filename)
        return pd.read_csv(path, index_col=0, float_precision="high")
    else:
        raise FileNotFoundError(f"{path} cannot be found")
