import os
import seaborn as sns
import warnings

from powersimdata.input.usa_tamu_model import TAMU
from powersimdata.input.mat_reader import MATReader


class Grid(object):
    """Grid

    """

    fields = {}

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

        self.fields['data_loc'] = data.data_loc
        self.fields['interconnect'] = data.interconnect
        self.fields['zone2id'] = data.zone2id
        self.fields['id2zone'] = data.id2zone
        self.fields['sub'] = data.sub
        self.fields['plant'] = data.plant
        self.fields['gencost'] = data.gencost
        self.fields['dcline'] = data.dcline
        self.fields['bus2sub'] = data.bus2sub
        self.fields['bus'] = data.bus
        self.fields['branch'] = data.branch
        self.fields['storage'] = data.storage
        self.fields['type2color'] = get_type2color()
        self.fields['id2type'] = get_id2type()
        self.fields['type2id'] = {value: key for key, value in
                                  self.fields['id2type'].items()}

    def __getattr__(self, field_name):
        """
        Overrides the object "." property interface to maintain backwards
        compatibility, i.e. grid.plant
        is the same as grid.fields["plant"]
        :param str field_name: grid field name as string
        :raises KeyError For attempts to use key not in the dictionary
        :return: property of the Grid class
        """
        if field_name == "__deepcopy__":
            return super().__deepcopy__
        if field_name == "__len__":
            return super().__len__
        if field_name == "__getstate__":
            return super().__getstate__
        else:
            try:
                warnings.warn(
                    "Grid property access is moving to dictionary indexing, "
                    "i.e. grid['branch'] consistent with REISE.jl",
                    DeprecationWarning
                )
                return self.fields[field_name]
            except AttributeError as e:
                print(e)

    def __getitem__(self, field_name):
        """
        Allows indexing into the resources dictionary directly from the
        object variable, i.e. grid["plant"] is the
        same as grid.fields["plant"]
        :param str field_name: grid field name as string
        :raises KeyError For attempts to use key not in the dictionary
        :return: property of the Grid class
        """
        try:
            return self.fields[field_name]
        except KeyError as e:
            print(e)


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
