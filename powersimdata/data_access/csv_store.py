import functools
import os
import shutil
from pathlib import Path
from tempfile import mkstemp

import pandas as pd

from powersimdata.utility import server_setup


def verify_hash(func):
    """Utility function which verifies the sha1sum of the file before writing
    it on the server. Operates on methods that return an updated scenario or
    execute list.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        checksum = self.data_access.checksum(self._FILE_NAME)
        table = func(self, *args, **kwargs)
        self.commit(table, checksum)
        return table

    return wrapper


class CsvStore:
    """Base class for common functionality used to manage scenario and execute
    list stored as csv files on the server

    :param powersimdata.data_access.data_access.DataAccess: data access object
    """

    def __init__(self, data_access):
        """Constructor"""
        self.data_access = data_access

    def get_table(self):
        """Read the given file from the server, falling back to local copy if
        unable to connect.

        :return: (*pandas.DataFrame*) -- the specified table as a data frame.
        """
        filename = self._FILE_NAME
        local_path = Path(server_setup.LOCAL_DIR, filename)

        try:
            self.data_access.copy_from(filename)
        except:  # noqa
            print(f"Failed to download {filename} from server")
            print("Falling back to local cache...")

        if local_path.is_file():
            return self._parse_csv(local_path)
        else:
            raise FileNotFoundError(f"{filename} does not exist locally.")

    def _parse_csv(self, file_object):
        """Read file from disk into data frame

        :param str, path object or file-like object file_object: a reference to
        the csv file
        :return: (*pandas.DataFrame*) -- the specified file as a data frame.
        """
        table = pd.read_csv(file_object)
        table.set_index("id", inplace=True)
        table.fillna("", inplace=True)
        return table.astype(str)

    def commit(self, table, checksum):
        """Save to local directory and upload if needed

        :param pandas.DataFrame table: the data frame to save
        :param str checksum: the checksum prior to download
        """
        tmp_file, tmp_path = mkstemp(dir=server_setup.LOCAL_DIR)
        table.to_csv(tmp_path)
        shutil.copy(tmp_path, os.path.join(server_setup.LOCAL_DIR, self._FILE_NAME))
        os.close(tmp_file)
        tmp_name = os.path.basename(tmp_path)
        self.data_access.push(tmp_name, checksum, change_name_to=self._FILE_NAME)
        if os.path.exists(tmp_path):  # only required if data_access is LocalDataAccess
            os.remove(tmp_path)
