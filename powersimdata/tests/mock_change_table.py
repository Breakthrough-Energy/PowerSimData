from powersimdata.input.change_table import ChangeTable


class MockChangeTable:
    def __init__(self, ct=None):
        """Constructor.

        :param dict ct: change table dict to be sent to ct attribute.
        """
        if ct is None:
            ct = {}
        self.ct = ct

    @property
    def __class__(self):
        """If anyone asks, I'm a ChangeTable object!"""
        return ChangeTable
