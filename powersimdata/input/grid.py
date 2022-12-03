from powersimdata.network.constants.carrier.storage import storage
from powersimdata.network.europe_tub.model import TUB, PyPSABase
from powersimdata.network.hifld.model import HIFLD
from powersimdata.network.usa_tamu.model import TAMU
from powersimdata.utility.helpers import MemoryCache, cache_key

_cache = MemoryCache()


class Grid:

    SUPPORTED_IMPORTS = {"pypsa"}
    SUPPORTED_MODELS = {"usa_tamu", "europe_tub"}

    """Grid

    :param str/iterable interconnect: geographical region covered. Either the region
        (e.g. USA), one of the interconnects in the region or a combination of the
        interconnects in the region. The full list of interconnects of the grid models
        is defined in :mod:`powersimdata.network.constants.model.model2interconnect`.
    :param str source: model used to build the network. Can be one of the supported
        models
    :raises TypeError: if source is not a string.
    :raises ValueError: if source is not a supported grid model.
    """

    def __init__(self, interconnect, source="usa_tamu", **kwargs):
        """Constructor."""
        if not isinstance(source, str):
            raise TypeError("source must be a str")
        supported = self.SUPPORTED_MODELS | self.SUPPORTED_IMPORTS
        if source not in supported:
            raise ValueError(f"Source must be one of {','.join(supported)} ")

        key = cache_key(interconnect, source)
        cached = _cache.get(key)
        if cached is not None:
            network = cached
        elif source == "usa_tamu":
            network = TAMU(interconnect)
        elif source == "hifld":
            network = HIFLD(interconnect)
        elif source == "europe_tub":
            network = TUB(interconnect, **kwargs)
        elif source == "pypsa":
            network = PyPSABase(interconnect, **kwargs)
        else:
            raise ValueError(f"Unknown source: {source}")

        network.build()

        self.data_loc = network.data_loc
        self.interconnect = network.interconnect
        self.zone2id = network.zone2id
        self.id2zone = network.id2zone
        self.sub = network.sub
        self.plant = network.plant
        self.gencost = network.gencost
        self.dcline = network.dcline
        self.bus2sub = network.bus2sub
        self.bus = network.bus
        self.branch = network.branch
        self.storage = network.storage
        self.grid_model = network.grid_model
        self.model_immutables = network.model_immutables

        _cache.put(key, network)

    def __repr__(self):
        result = self.__class__.__name__
        result += f"\ninterconnect: {self.interconnect}\n"
        result += f"model: {self.model_immutables.model}\n"
        result += f"data_loc: {self.data_loc}\n"
        df_name = ["sub", "plant", "dcline", "bus2sub", "bus", "branch"]
        for n in df_name:
            shape = getattr(self, n).shape
            result += f"{n}: {shape}\n"
        result += f"id2zone: {len(self.id2zone)}\n"
        result += f"zone2id: {len(self.zone2id)}"
        return result

    def __eq__(self, other):
        """Used when 'self == other' is evaluated.

        :param object other: other object to be compared against.
        :return: (*bool*).
        """

        def _univ_eq(ref, test, failure_flag=None):
            """Check for {boolean, dataframe, or column data} equality.

            :param object ref: one object to be tested (order does not matter).
            :param object test: another object to be tested.
            :param str failure_flag: flag to add to nonmatching_entries on failure.
            :raises AssertionError: if no equality can be confirmed (w/o failure_flag).
            """
            try:
                try:
                    test_eq = ref == test
                    if isinstance(test_eq, bool):
                        assert test_eq
                    else:
                        assert test_eq.all().all()
                except ValueError:
                    assert set(ref.columns) == set(test.columns)
                    for col in ref.columns:
                        assert (ref[col] == test[col]).all()
            except (AssertionError, ValueError):
                if failure_flag is None:
                    raise
                else:
                    nonmatching_entries.add(failure_flag)

        if not isinstance(other, Grid):
            err_msg = "Unable to compare Grid & %s" % type(other).__name__
            raise NotImplementedError(err_msg)

        nonmatching_entries = set()
        # compare gencost
        # Comparing gencost['after'] will fail if one Grid was linearized
        _univ_eq(self.gencost["before"], other.gencost["before"], "gencost")

        # compare storage
        _univ_eq(len(self.storage["gen"]), len(other.storage["gen"]), "storage")
        _univ_eq(self.storage.keys(), other.storage.keys(), "storage")
        ignored_subkeys = {"gencost"} | set(storage.keys())
        for subkey in set(self.storage.keys()) - ignored_subkeys:
            # REISE will modify some gen columns
            self_data = self.storage[subkey]
            other_data = other.storage[subkey]
            if subkey == "gen":
                excluded_cols = ["ramp_10", "ramp_30"]
                self_data = self_data.drop(excluded_cols, axis=1)
                other_data = other_data.drop(excluded_cols, axis=1)
            _univ_eq(self_data, other_data, "storage")

        # compare bus
        # MOST changes BUS_TYPE for buses with DC Lines attached
        _univ_eq(self.bus.drop("type", axis=1), other.bus.drop("type", axis=1), "bus")
        # compare plant
        # REISE does some modifications to Plant data
        excluded_cols = ["status", "Pmin", "ramp_10", "ramp_30"]
        self_df = self.plant.drop(excluded_cols, axis=1)
        other_df = other.plant.drop(excluded_cols, axis=1)
        _univ_eq(self_df, other_df, "plant")
        # compare branch
        _univ_eq(self.branch, other.branch, "branch")
        # compare dcline
        _univ_eq(self.dcline, other.dcline, "dcline")
        # compare sub
        _univ_eq(self.sub, other.sub, "sub")
        # check grid helper attribute equalities
        _univ_eq(self.zone2id, other.zone2id, "zone2id")
        _univ_eq(self.id2zone, other.id2zone, "id2zone")
        _univ_eq(self.bus2sub, other.bus2sub, "bus2sub")

        if len(nonmatching_entries) > 0:
            print(f"non-matching entries: {', '.join(sorted(nonmatching_entries))}")
            return False
        return True
