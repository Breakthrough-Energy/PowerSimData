import os

from powersimdata.input.abstract_grid import AbstractGrid


class HIFLD(AbstractGrid):
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


def check_and_format_interconnect(interconnect):
    # Placeholder for now
    return interconnect


def interconnect_to_name(interconnect):
    # Placeholder for now
    return interconnect
