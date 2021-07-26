import pandas as pd

from powersimdata.input import const
from powersimdata.utility.helpers import MemoryCache, cache_key


class AbstractGrid:
    """Grid Builder."""

    def __init__(self):
        """Constructor"""
        self.data_loc = None
        self.interconnect = None
        self.zone2id = {}
        self.id2zone = {}
        self.sub = pd.DataFrame()
        self.plant = pd.DataFrame()
        self.gencost = {"before": pd.DataFrame(), "after": pd.DataFrame()}
        self.dcline = pd.DataFrame()
        self.bus2sub = pd.DataFrame()
        self.bus = pd.DataFrame()
        self.branch = pd.DataFrame()
        self.storage = storage_template()


def storage_template():
    """Get storage

    :return: (*dict*) -- storage structure for MATPOWER/MOST
    """
    storage = {
        "gen": pd.DataFrame(columns=const.col_name_plant),
        "gencost": pd.DataFrame(columns=const.col_name_gencost),
        "StorageData": pd.DataFrame(columns=const.col_name_storage_storagedata),
        "genfuel": [],
        "duration": None,  # hours
        "min_stor": None,  # ratio
        "max_stor": None,  # ratio
        "InEff": None,
        "OutEff": None,
        "LossFactor": None,  # stored energy fraction / hour
        "energy_price": None,  # $/MWh
        "terminal_min": None,
        "terminal_max": None,
    }
    return storage


class AbstractGridFactory:
    _cache = MemoryCache()

    @classmethod
    def get_or_create(cls, abstract_grid_class, *args):
        assert(issubclass(abstract_grid_class, AbstractGrid))
        key = cache_key(abstract_grid_class.__name__, *args)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached

        new_abstract_grid = abstract_grid_class.__init__(*args)
        cls._cache.put(key, new_abstract_grid)
        return new_abstract_grid
