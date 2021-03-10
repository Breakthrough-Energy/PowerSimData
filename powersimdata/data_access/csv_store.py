import os
from pathlib import Path

import pandas as pd

from powersimdata.utility import server_setup


class CsvStore:
    """Base class for common functionality used to manage scenario and execute
    list stored as csv files on the server

    :param powersimdata.data_access.data_access.DataAccess: data access object
    """

    def __init__(self, data_access):
        """Constructor"""
        self.data_access = data_access

    def get_table(self, filename):
        """Read the given file from the server, falling back to local copy if
        unable to connect.

        :return: (*pandas.DataFrame*) -- the specified table as a data frame.
        """
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

    def _save_file(self, table):
        """Save to local directory

        :param pandas.DataFrame table: the data frame to save
        """
        table.to_csv(os.path.join(server_setup.LOCAL_DIR, self._FILE_NAME))
