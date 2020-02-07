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
        elif source == 'output':
            data = MATReader()
        else:
            raise ValueError('%s not implemented' % source)

        for key, value in vars(data).items():
            setattr(self, key, value)
