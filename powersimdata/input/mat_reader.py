import os

from powersimdata.input.abstract_grid import AbstractGrid


class MATReader(AbstractGrid):
    """MATLAB file reader

    """
    def __init__(self, filename):
        """Constructor.

        :param filename: path to file
        """
        super().__init__()
        self._set_data_loc(filename)

    def _set_data_loc(self, filename):
        """Sets data location.

        :param str filename: path to file
        :raises IOError: if file does not exist.
        """
        if os.path.isfile(filename) is False:
            raise IOError('%s file not found' % filename)
        else:
            self.data_loc = filename
