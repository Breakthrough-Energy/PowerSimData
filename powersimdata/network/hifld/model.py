import os

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.network.hifld.constants.storage import defaults


class HIFLD(AbstractGrid):
    """HIFLD network.

    :param str/iterable interconnect: interconnect name(s).
    """

    def __init__(self, interconnect):
        """Constructor."""
        super().__init__()

        self._set_data_loc(os.path.dirname(__file__))
        self._build_network(interconnect, "hifld")
        self.storage.update(defaults)
