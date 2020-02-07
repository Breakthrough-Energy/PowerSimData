from powersimdata.input.change_table import ChangeTable


class MockChangeTable:
    def __init__(self, grid, ct=None):
        """Constructor.

        :param powersimdata.input.grid.Grid grid: instance of Grid object.
        :param dict ct: change table dict to be sent to ct attribute.
        """
        self.grid = grid
        if ct is None:
            ct = {}
        self.ct = ct

    @property
    def __class__(self):
        """If anyone asks, I'm a ChangeTable object!"""
        return ChangeTable
