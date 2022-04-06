from powersimdata.data_access.context import Context
from powersimdata.utility.helpers import MemoryCache, cache_key

_cache = MemoryCache()


class InputBase:
    """Load input data."""

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
        raise NotImplementedError

    def _read(self, f, path):
        raise NotImplementedError

    def get_data(self, scenario_info, field_name):
        """Returns data either from server or local directory.

        :param dict scenario_info: scenario information.
        :param str field_name: defined by subclass
        :return: (*pandas.DataFrame*, *dict*, or *str*) -- implementation dependent
        """
        self._check_field(field_name)
        print("--> Loading %s" % field_name)

        filepath = self._get_file_path(scenario_info, field_name)

        key = cache_key(filepath)
        cached = _cache.get(key)
        if cached is not None:
            return cached
        with self.data_access.get(filepath) as (f, path):
            data = self._read(f, path)
        _cache.put(key, data)
        return data
