from powersimdata.scenario.create import _Builder
from powersimdata.tests.mock_change_table import MockChangeTable


class MockBuilder:
    def __init__(self, ct=None):
        """Constructor.

        :param dict ct: change table dict to be sent to MockChangeTable.
        """
        if ct is None:
            ct = {}
        self.change_table = MockChangeTable(ct)

    @property
    def __class__(self):
        """If anyone asks, I'm a _Builder object!"""
        return _Builder
