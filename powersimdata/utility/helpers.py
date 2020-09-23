import copy
import os
import sys


class MemoryCache:
    def __init__(self):
        self._cache = {}

    def put(self, key, obj):
        self._cache[key] = obj

    def get(self, key):
        if key in self._cache.keys():
            return copy.deepcopy(self._cache[key])

    def list_keys(self):
        keys = list(self._cache.keys())
        print(keys)
        return keys


def cache_key(*args):
    kb = CacheKeyBuilder(*args)
    return kb.build()


class CacheKeyBuilder:
    def __init__(self, *args):
        self.args = args

    def build(self):
        return tuple(self._build(a) for a in self.args)

    def _build(self, arg):
        if isinstance(arg, (str, int, bool)):
            return str(arg)
        if isinstance(arg, (list, set, tuple)):
            return "-".join(self._build(a) for a in arg)
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
