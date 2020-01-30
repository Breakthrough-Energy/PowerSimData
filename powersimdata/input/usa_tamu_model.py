import os
import pandas as pd
import seaborn as sns

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.mpc_reader import MPCReader, get_storage
from powersimdata.input.helpers import (csv_to_data_frame,
                                        add_column_to_data_frame)


class TAMU(AbstractGrid):
    """TAMU network.

    """
    def __init__(self, interconnect):
        """Constructor.

        :param list interconnect: interconnect name(s).
        """
        super().__init__()
        self._set_data_loc()

        if check_interconnect(interconnect):
            self.interconnect = interconnect
            self._build_network()
            self.type2color = get_type2color()
            self.id2type = get_id2type()
            self.type2id = {value: key for key, value in self.id2type.items()}

    def _set_data_loc(self):
        """Sets data location.

        :raises IOError: if directory does not exist.
        """
        top_dirname = os.path.dirname(__file__)
        data_loc = os.path.join(top_dirname, 'data', 'usa_tamu')
        if os.path.isdir(data_loc) is False:
            raise IOError('%s directory not found' % data_loc)
        else:
            self.data_loc = data_loc

    def _set_storage(self):
        """Sets storage properties.

        """
        self.storage = get_storage()
        self.storage['duration'] = 4
        self.storage['min_stor'] = 0.05
        self.storage['max_stor'] = 0.95
        self.storage['InEff'] = 0.9
        self.storage['OutEff'] = 0.9
        self.storage['energy_price'] = 20

    def _build_network(self):
        """Build network.

        """
        reader = MPCReader(self.data_loc)
        for key, value in vars(reader).items():
            setattr(self, key, value)

        self._set_storage()

        add_information_to_model(self)

        if 'USA' not in self.interconnect:
            self._drop_interconnect()

    def _drop_interconnect(self):
        """Trim data frames to only keep information pertaining to the user
            defined interconnect(s)

        """
        for key, value in self.__dict__.items():
            if key in ['sub', 'bus2sub', 'bus', 'plant', 'gencost', 'branch']:
                value.query('interconnect == @self.interconnect', inplace=True)
            elif key == 'dcline':
                value.query('from_interconnect == @self.interconnect &'
                            'to_interconnect == @self.interconnect',
                            inplace=True)
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
    possible = ['Eastern', 'Texas', 'Western', 'USA']
    if not isinstance(interconnect, list):
        raise TypeError("List of string(s) is expected for interconnect")

    for i in interconnect:
        if i not in possible:
            raise ValueError("Wrong interconnect. Choose from %s" %
                             " | ".join(possible))
    n = len(interconnect)
    if n > len(set(interconnect)):
        raise ValueError("List of interconnects contains duplicate values")
    if 'USA' in interconnect and n > 1:
        raise ValueError("USA interconnect cannot be paired")

    return True


def get_type2color():
    """Defines generator type to generator color mapping for TAMU. Used for
        plotting.

    :return: (*dict*) -- generator type to color mapping.
    """
    type2color = {
        'wind': sns.xkcd_rgb["green"],
        'solar': sns.xkcd_rgb["amber"],
        'hydro': sns.xkcd_rgb["light blue"],
        'ng': sns.xkcd_rgb["orchid"],
        'nuclear': sns.xkcd_rgb["silver"],
        'coal': sns.xkcd_rgb["light brown"],
        'geothermal': sns.xkcd_rgb["hot pink"],
        'dfo': sns.xkcd_rgb["royal blue"],
        'biomass': sns.xkcd_rgb["dark green"],
        'other': sns.xkcd_rgb["melon"],
        'storage': sns.xkcd_rgb["orange"]}
    return type2color


def get_id2type():
    """Defines generator type to generator id mapping.

    :return: (*tuple*) -- generator type to generator id mapping.
    """
    id2type = {
        0: 'wind',
        1: 'solar',
        2: 'hydro',
        3: 'ng',
        4: 'nuclear',
        5: 'coal',
        6: 'geothermal',
        7: 'dfo',
        8: 'biomass',
        9: 'other',
        10: 'storage'}
    return id2type


def add_information_to_model(model):
    """Adds information to TAMU model.

    :param powersimdata.input.TAMU model: TAMU instance.
    :return: (*powersimdata.input.TAMU*) -- modified TAMU model.
    """
    model.sub = csv_to_data_frame(model.data_loc, 'sub.csv')
    model.bus2sub = csv_to_data_frame(model.data_loc, 'bus2sub.csv')
    model.id2zone = csv_to_data_frame(
        model.data_loc, 'zone.csv').zone_name.to_dict()
    model.zone2id = {v: k for k, v in model.id2zone.items()}

    bus2zone = model.bus.zone_id.to_dict()
    bus2coord = pd.merge(
        model.bus2sub[['sub_id']],
        model.sub[['lat', 'lon']],
        on='sub_id').set_index(
        model.bus2sub.index).drop(columns='sub_id').to_dict()

    def get_lat(idx):
        return [bus2coord['lat'][i] for i in idx]

    def get_lon(idx):
        return [bus2coord['lon'][i] for i in idx]

    def get_zone_id(idx):
        return [bus2zone[i] for i in idx]

    def get_zone_name(idx):
        return [model.id2zone[bus2zone[i]] for i in idx]

    extra_col_bus = {
        'lat': get_lat(model.bus.index),
        'lon': get_lon(model.bus.index)}
    model.bus = add_column_to_data_frame(model.bus, extra_col_bus)

    extra_col_plant = {
        'lat': get_lat(model.plant.bus_id),
        'lon': get_lon(model.plant.bus_id),
        'zone_id': get_zone_id(model.plant.bus_id),
        'zone_name': get_zone_name(model.plant.bus_id)}
    model.plant = add_column_to_data_frame(model.plant, extra_col_plant)

    extra_col_branch = {
        'from_zone_id': get_zone_id(model.branch.from_bus_id),
        'to_zone_id': get_zone_id(model.branch.to_bus_id),
        'from_zone_name': get_zone_name(model.branch.from_bus_id),
        'to_zone_name': get_zone_name(model.branch.to_bus_id),
        'from_lat': get_lat(model.branch.from_bus_id),
        'from_lon': get_lon(model.branch.from_bus_id),
        'to_lat': get_lat(model.branch.to_bus_id),
        'to_lon': get_lon(model.branch.to_bus_id)}
    model.branch = add_column_to_data_frame(model.branch, extra_col_branch)
    return model
