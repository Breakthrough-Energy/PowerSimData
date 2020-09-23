import os
import sys


class MemoryCache:
    def __init__(self):
        self._cache = {}

    def put(self, key, obj):
        self._cache[key] = obj

    def get(self, key):
        if key in self._cache.keys():
            return self._cache[key]

    def list_keys(self):
        keys = list(self._cache.keys())
        print(keys)
        return keys


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
