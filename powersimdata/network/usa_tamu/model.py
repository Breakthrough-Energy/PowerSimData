import os

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.helpers import (
    add_coord_to_grid_data_frames,
    add_zone_to_grid_data_frames,
    csv_to_data_frame,
)
from powersimdata.network.csv_reader import CSVReader
from powersimdata.network.usa_tamu.constants.storage import defaults
from powersimdata.network.usa_tamu.constants.zones import (
    abv2state,
    interconnect2loadzone,
    loadzone,
    state2loadzone,
)


class TAMU(AbstractGrid):
    """TAMU network.

    :param list interconnect: interconnect name(s).
    """

    def __init__(self, interconnect):
        """Constructor."""
        super().__init__()
        self._set_data_loc()

        if check_interconnect(interconnect):
            self.interconnect = interconnect
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


def check_interconnect(interconnect):
    """Checks interconnect.

    :param list interconnect: interconnect name(s).
    :raises TypeError: if parameter has wrong type.
    :raises Exception: if interconnect not found or combination of
        interconnect is not appropriate.
    :return: (*bool*) -- if valid
    """
    possible = ["Eastern", "Texas", "Western", "USA"]
    if not isinstance(interconnect, list):
        raise TypeError("List of string(s) is expected for interconnect")

    for i in interconnect:
        if i not in possible:
            raise ValueError(
                "Wrong interconnect. Choose from %s" % " | ".join(possible)
            )
    n = len(interconnect)
    if n > len(set(interconnect)):
        raise ValueError("List of interconnects contains duplicate values")
    if "USA" in interconnect and n > 1:
        raise ValueError("USA interconnect cannot be paired")

    return True


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


def area_to_loadzone(area, area_type=None):
    """Map the query area to a list of loadzones

    :param str area: one of: *loadzone*, *state*, *state abbreviation*,
        *interconnect*, *'all'*
    :param str area_type: one of: *'loadzone'*, *'state'*,
        *'state_abbr'*, *'interconnect'*
    :return: (*set*) -- set of loadzone names associated with the query area.
    :raise TypeError: if area is not None or str
    :raise ValueError: if area is invalid or the combination of area and area_type is invalid

    .. note:: if area_type is not specified, the function will check the
        area in the order of 'state', 'loadzone', 'state abbreviation',
        'interconnect' and 'all'.
    """

    def raise_invalid_area(area_type):
        raise ValueError("Invalid area for area_type=%s" % area_type)

    if area_type is not None and not isinstance(area_type, str):
        raise TypeError("'area_type' should be either None or str.")
    if area_type:
        if area_type == "loadzone":
            if area in loadzone:
                loadzone_set = {area}
            else:
                raise_invalid_area(area_type)
        elif area_type == "state":
            if area in list(abv2state.values()):
                loadzone_set = state2loadzone[area]
            else:
                raise_invalid_area(area_type)
        elif area_type == "state_abbr":
            if area in abv2state:
                loadzone_set = state2loadzone[abv2state[area]]
            else:
                raise_invalid_area(area_type)
        elif area_type == "interconnect":
            if area in {"Texas", "Western", "Eastern"}:
                loadzone_set = interconnect2loadzone[area]
            else:
                raise_invalid_area(area_type)
        else:
            print(
                "%s is incorrect. Available area_types are 'loadzone',"
                "'state', 'state_abbr', 'interconnect'." % area_type
            )
            raise ValueError("Invalid area_type")
    else:
        if area in list(abv2state.values()):
            loadzone_set = state2loadzone[area]
        elif area in loadzone:
            loadzone_set = {area}
        elif area in abv2state:
            loadzone_set = state2loadzone[abv2state[area]]
        elif area in {"Texas", "Western", "Eastern"}:
            loadzone_set = interconnect2loadzone[area]
        elif area == "all":
            loadzone_set = loadzone
        else:
            print("%s is incorrect." % area)
            raise ValueError("Invalid area")
    return loadzone_set
