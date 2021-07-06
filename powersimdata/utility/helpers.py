import copy
import importlib
import os
import sys


class MemoryCache:
    """Wrapper around a dict object that exposes a cache interface. Users should
    create a separate instance for each distinct use case.
    """

    def __init__(self):
        """Constructor"""
        self._cache = {}

    def put(self, key, obj):
        """Add or set the value for the given key.

        :param tuple key: a tuple used to lookup the cached value
        :param Any obj: the object to cache
        """
        self._cache[key] = copy.deepcopy(obj)

    def get(self, key):
        """Retrieve the value associated with key if it exists.

        :param tuple key: the cache key
        :return: (*Any* or *NoneType*) -- the cached value if found, or None
        """
        if key in self._cache.keys():
            return copy.deepcopy(self._cache[key])

    def list_keys(self):
        """Return and print the current cache keys.

        :return: (*list*) -- the list of cache keys
        """
        keys = list(self._cache.keys())
        print(keys)
        return keys


def cache_key(*args):
    """Creates a cache key from the given args. The user should ensure that the
    range of inputs will not result in key collisions.

    :param args: variable length argument list
    :return: (*tuple*) -- a tuple containing the input in heirarchical
        structure
    """
    kb = CacheKeyBuilder(*args)
    return kb.build()


class CacheKeyBuilder:
    """Helper class to generate cache keys

    :param args: variable length arguments from which to build a key
    """

    def __init__(self, *args):
        """Constructor"""
        self.args = args

    def build(self):
        """Combine args into a tuple, preserving the structure of each element.

        :return: (*tuple*) -- container which can be used as a cache key
        """
        return self._build(self.args)

    def _build(self, arg):
        if arg is None:
            return "null"
        if isinstance(arg, (str, int, bool)):
            return arg
        if isinstance(arg, (list, set, tuple)):
            return tuple(self._build(a) for a in arg)
        raise ValueError(f"unsupported type for cache key = {type(arg)}")


class PrintManager:
    """Manages print messages."""

    def __init__(self):
        """Constructor"""
        self.stdout = sys.stdout

    def __enter__(self):
        self.block_print()

    def __exit__(self, exc_type, exc_value, traceback):
        self.enable_print()

    @staticmethod
    def block_print():
        """Suppresses print"""
        sys.stdout = open(os.devnull, "w")

    def enable_print(self):
        """Enables print"""
        sys.stdout = self.stdout


def _check_import(package_name):
    """Import a package, or give a useful error message if it's not there."""
    try:
        return importlib.import_module(package_name)
    except ImportError:
        err_msg = (
            f"{package_name} is not installed. "
            "It may be an optional powersimdata requirement."
        )
        raise ImportError(err_msg)
