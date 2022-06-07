import os

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.converter.helpers import (
    add_coord_to_grid_data_frames,
    add_zone_to_grid_data_frames,
)
from powersimdata.network.constants.model import model2region
from powersimdata.network.csv_reader import CSVReader


class FromCSV(AbstractGrid):
    """Grid Builder for grid model enclosed in CSV files."""

    def _set_data_loc(self, top_dirname):
        """Sets data location.

        :param str top_dirname: name of directory enclosing data.
        :raises IOError: if directory does not exist.
        """
        data_loc = os.path.join(top_dirname, "data")
        if os.path.isdir(data_loc) is False:
            raise IOError("%s directory not found" % data_loc)
        else:
            self.data_loc = data_loc

    def _build(self, interconnect, grid_model):
        """Build network.

        :param list interconnect: interconnect name(s).
        :param str model: the grid model.
        """
        reader = CSVReader(self.data_loc)
        self.bus = reader.bus
        self.plant = reader.plant
        self.branch = reader.branch
        self.dcline = reader.dcline
        self.gencost["after"] = self.gencost["before"] = reader.gencost
        self.sub = reader.sub
        self.bus2sub = reader.bus2sub
        self.id2zone = reader.zone["zone_name"].to_dict()
        self.zone2id = {v: k for k, v in self.id2zone.items()}

        self._add_information()

        if model2region[grid_model] not in interconnect:
            self._drop_interconnect(interconnect)

    def _add_information(self):
        add_zone_to_grid_data_frames(self)
        add_coord_to_grid_data_frames(self)

    def _drop_interconnect(self, interconnect):
        """Trim data frames to only keep information pertaining to the user
        defined interconnect(s).

        :param list interconnect: interconnect name(s).
        """
        for key, value in self.__dict__.items():
            if key in ["sub", "bus2sub", "bus", "plant", "branch"]:
                value.query("interconnect == @interconnect", inplace=True)
            elif key == "gencost":
                value["before"].query("interconnect == @interconnect", inplace=True)
            elif key == "dcline":
                value.query(
                    "from_interconnect == @interconnect &"
                    "to_interconnect == @interconnect",
                    inplace=True,
                )
        self.id2zone = {k: self.id2zone[k] for k in self.bus.zone_id.unique()}
        self.zone2id = {value: key for key, value in self.id2zone.items()}
