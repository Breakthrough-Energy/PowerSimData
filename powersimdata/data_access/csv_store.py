import functools

import pandas as pd


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


def _parse_csv(file_object):
    """Read file from disk into data frame

    :param str, path object or file-like object file_object: a reference to
    the csv file
    :return: (*pandas.DataFrame*) -- the specified file as a data frame.
    """
    table = pd.read_csv(file_object)
    table.set_index("id", inplace=True)
    table.fillna("", inplace=True)
    return table.astype(str)


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
        try:
            return self._get_table(filename)
        except:  # noqa
            return self._get_table(filename + ".2")

    def _get_table(self, filename):
        self.data_access.copy_from(filename)
        with self.data_access.get(filename) as (f, _):
            return _parse_csv(f)

    def commit(self, table, checksum):
        """Save to local directory and upload if needed

        :param pandas.DataFrame table: the data frame to save
        :param str checksum: the checksum prior to download
        """
        with self.data_access.push(self._FILE_NAME, checksum) as f:
            table.to_csv(f)
