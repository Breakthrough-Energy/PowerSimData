import os

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.helpers import (
    add_coord_to_grid_data_frames,
    add_zone_to_grid_data_frames,
    csv_to_data_frame,
)
from powersimdata.network.csv_reader import CSVReader
from powersimdata.network.usa_tamu.constants.storage import defaults


class TAMU(AbstractGrid):
    """TAMU network.

    :param str/list interconnect: interconnect name(s).
    """

    def __init__(self, interconnect):
        """Constructor."""
        super().__init__()
        self._set_data_loc()

        self.interconnect = check_and_format_interconnect(interconnect)
        self._build_network()

    def _set_data_loc(self):
        """Sets data location.

        :raises IOError: if directory does not exist.
        """
        top_dirname = os.path.dirname(__file__)
        data_loc = os.path.join(top_dirname, "data")
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

        self.storage.update(defaults)

        add_information_to_model(self)

        if "USA" not in self.interconnect:
            self._drop_interconnect()

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


def check_and_format_interconnect(interconnect):
    """Checks interconnect.

    :param str/iterable interconnect: interconnect name(s).
    :return: (*list*) -- interconnect(s)
    :raises TypeError: if parameter has wrong type.
    :raises ValueError: if interconnect not found or combination of interconnect is not
        appropriate.
    """
    if isinstance(interconnect, str):
        interconnect = [interconnect]
    try:
        interconnect = sorted(set(interconnect))
    except:  # noqa
        raise TypeError("interconnect must be either str or an iterable of str")

    possible = ["Eastern", "Texas", "Western", "USA"]
    if any(i for i in interconnect if i not in possible):
        raise ValueError("Wrong interconnect. Choose from %s" % " | ".join(possible))
    n = len(interconnect)
    if "USA" in interconnect and n > 1:
        raise ValueError("USA cannot be paired")
    if n == 3:
        raise ValueError("Use USA instead")

    return interconnect


def interconnect_to_name(interconnect):
    """Return name of interconnect or collection of interconnects..

    :param list interconnect: interconnect name(s).
    """
    return "_".join(sorted(check_and_format_interconnect(interconnect)))


def add_information_to_model(model):
    """Adds information to TAMU model. This is done inplace.

    :param powersimdata.input.TAMU model: TAMU instance.
    """
    model.sub = csv_to_data_frame(model.data_loc, "sub.csv")
    model.bus2sub = csv_to_data_frame(model.data_loc, "bus2sub.csv")
    model.id2zone = csv_to_data_frame(model.data_loc, "zone.csv").zone_name.to_dict()
    model.zone2id = {v: k for k, v in model.id2zone.items()}

    add_zone_to_grid_data_frames(model)
    add_coord_to_grid_data_frames(model)
