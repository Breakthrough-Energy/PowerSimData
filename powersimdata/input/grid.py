import os
import seaborn as sns

from powersimdata.input.usa_tamu_model import TAMU
from powersimdata.input.mat_reader import MATReader


class Grid(object):
    """Grid

    """
    def __init__(self, interconnect, source='usa_tamu'):
        """Constructor

        :param list interconnect: interconnect name(s).
        :param str source: model used to build the network
        :raises TypeError: if source is not a string.
        :raises ValueError: if model does not exist.
        """
        if not isinstance(source, str):
            raise TypeError('source must be a string')
        if source == 'usa_tamu':
            data = TAMU(interconnect)
        elif os.path.splitext(source)[1] == '.mat':
            data = MATReader(source)
        else:
            raise ValueError('%s not implemented' % source)

        self.data_loc = data.data_loc
        self.interconnect = data.interconnect
        self.zone2id = data.zone2id
        self.id2zone = data.id2zone
        self.sub = data.sub
        self.plant = data.plant
        self.gencost = data.gencost
        self.dcline = data.dcline
        self.bus2sub = data.bus2sub
        self.bus = data.bus
        self.branch = data.branch
        self.storage = data.storage
        self.type2color = get_type2color()
        self.id2type = get_id2type()
        self.type2id = {value: key for key, value in self.id2type.items()}


def get_type2color():
    """Defines generator type to generator color mapping. Used for plotting.

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
