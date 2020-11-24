import copy
import importlib
import os
import sys


class CommandBuilder:
    @staticmethod
    def copy(src, dest, recursive=False, update=False):
        r_flag = "R" if recursive else ""
        u_flag = "u" if update else ""
        p_flag = "p"
        flags = f"-{r_flag}{u_flag}{p_flag}"
        return fr"\cp {flags} {src} {dest}"

    @staticmethod
    def remove(target, recursive=False, force=False):
        r_flag = "r" if recursive else ""
        f_flag = "f" if force else ""
        if recursive or force:
            flags = f"-{r_flag}{f_flag}"
            return f"rm {flags} {target}"
        return f"rm {target}"


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
        self._cache[key] = obj

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


class PrintManager(object):
    """Manages print messages."""

    def __init__(self):
        """Constructor"""
        self.stdout = sys.stdout

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
