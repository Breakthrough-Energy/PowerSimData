import os

from powersimdata.data_access.data_access import TempDataAccess, get_blob_fs
from powersimdata.utility import templates


class MockContext:
    def __init__(self):
        self.data_access = self._setup()

    def get_data_access(self, ignored=None):
        return self.data_access

    def _setup(self):
        tda = TempDataAccess()
        tda.fs.add_fs("profile_fs", get_blob_fs("profiles"), priority=2)
        for path in ("ExecuteList.csv", "ScenarioList.csv"):
            orig = os.path.join(templates.__path__[0], path)
            with open(orig, "rb") as f:
                tda.fs.upload(path, f)
        return tda
