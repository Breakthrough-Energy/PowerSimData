from powersimdata.data_access.context import Context
from powersimdata.utility.helpers import MemoryCache, cache_key

_cache = MemoryCache()


class InputBase:
    """Define abstract methods and common implementation for subclasses that interact
    with scenario input data.
    """

    def __init__(self):
        """Constructor."""
        self.data_access = Context.get_data_access()
        self._file_extension = {}

    def _check_field(self, field_name):
        """Checks field name.

        :param str field_name: defined by subclass
        :raises ValueError: if invalid field name is given
        """
        possible = list(self._file_extension.keys())
        if field_name not in possible:
            raise ValueError("Only %s data can be loaded" % " | ".join(possible))

    def _get_file_path(self, scenario_info, field_name):
        """Get the path to a file for the scenario

        :param dict scenario_info: metadata for a scenario.
        :param str field_name: defined by subclass
        :return: (*str*) -- the pyfilesystem path to the file
        """
        raise NotImplementedError

    def _read(self, f, path):
        """Read content from file object into data frame

        :param io.IOBase f: an open file object
        :param str path: the file path
        :return: (*object*) -- implementation dependent
        """
        raise NotImplementedError

    def get_data(self, scenario_info, field_name):
        """Returns data from (possibly remote) filesystem and cache
        the result in memory.

        :param dict scenario_info: scenario information.
        :param str field_name: defined by subclass
        :return: (*object*) -- implementation dependent
        """
        self._check_field(field_name)
        print("--> Loading %s" % field_name)

        filepath = self._get_file_path(scenario_info, field_name)
        return self._get_data_internal(filepath)

    def _get_data_internal(self, filepath):
        key = cache_key(filepath)
        cached = _cache.get(key)
        if cached is not None:
            return cached
        with self.data_access.get(filepath) as (f, path):
            data = self._read(f, path)
        _cache.put(key, data)
        return data
