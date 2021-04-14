import os

import pandas as pd

from powersimdata.input import const
from powersimdata.input.helpers import (
    add_coord_to_grid_data_frames,
    add_zone_to_grid_data_frames,
    csv_to_data_frame,
)
from powersimdata.network.csv_reader import CSVReader


class AbstractGrid:
    """Grid Builder. Child classes must assign self.top_dirname and
    self.umbrella_interconnect before self.__init__ is called, or re-define the __init__
    and/or methods called within the __init__ to avoid an AttributeError.
    """

    def __init__(self):
        """Constructor"""
        self.data_loc = None
        self.zone2id = {}
        self.id2zone = {}
        self.sub = pd.DataFrame()
        self.plant = pd.DataFrame()
        self.gencost = {"before": pd.DataFrame(), "after": pd.DataFrame()}
        self.dcline = pd.DataFrame()
        self.bus2sub = pd.DataFrame()
        self.bus = pd.DataFrame()
        self.branch = pd.DataFrame()
        self.storage = storage_template()
        self._set_data_loc()
        self._build_network()

    def _set_data_loc(self):
        """Sets data location.

        :raises IOError: if directory does not exist.
        """
        data_loc = os.path.join(self.top_dirname, "data")
        if os.path.isdir(data_loc) is False:
            raise IOError("%s directory not found" % data_loc)
        else:
            self.data_loc = data_loc

    def _build_network(self):
        """Build network."""
        reader = CSVReader(self.data_loc)
        self.bus = reader.bus
        self.plant = reader.plant
        self.branch = reader.branch
        self.dcline = reader.dcline
        self.gencost["after"] = self.gencost["before"] = reader.gencost

        self._add_information_to_model()

        if self.umbrella_interconnect not in self.interconnect:
            self._drop_interconnect()

    def _add_information_to_model(self):
        self.sub = csv_to_data_frame(self.data_loc, "sub.csv")
        self.bus2sub = csv_to_data_frame(self.data_loc, "bus2sub.csv")
        self.id2zone = csv_to_data_frame(self.data_loc, "zone.csv").zone_name.to_dict()
        self.zone2id = {v: k for k, v in self.id2zone.items()}

        add_zone_to_grid_data_frames(self)
        add_coord_to_grid_data_frames(self)

    def _drop_interconnect(self):
        """Trim data frames to only keep information pertaining to the user
        defined interconnect(s).

        """
        for key, value in self.__dict__.items():
            if key in ["sub", "bus2sub", "bus", "plant", "branch"]:
                value.query("interconnect == @self.interconnect", inplace=True)
            elif key == "gencost":
                value["before"].query(
                    "interconnect == @self.interconnect", inplace=True
                )
            elif key == "dcline":
                value.query(
                    "from_interconnect == @self.interconnect &"
                    "to_interconnect == @self.interconnect",
                    inplace=True,
                )
        self.id2zone = {k: self.id2zone[k] for k in self.bus.zone_id.unique()}
        self.zone2id = {value: key for key, value in self.id2zone.items()}


def storage_template():
    """Get storage

    :return: (*dict*) -- storage structure for MATPOWER/MOST
    """
    storage = {
        "gen": pd.DataFrame(columns=const.col_name_plant),
        "gencost": pd.DataFrame(columns=const.col_name_gencost),
        "StorageData": pd.DataFrame(columns=const.col_name_storage_storagedata),
        "genfuel": [],
        "duration": None,  # hours
        "min_stor": None,  # ratio
        "max_stor": None,  # ratio
        "InEff": None,
        "OutEff": None,
        "LossFactor": None,  # stored energy fraction / hour
        "energy_price": None,  # $/MWh
        "terminal_min": None,
        "terminal_max": None,
    }
    return storage
