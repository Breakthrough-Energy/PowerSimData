import os

from powersimdata.input.scenario_grid import FromREISE, FromREISEjl
from powersimdata.network.usa_tamu.constants import storage as tamu_storage
from powersimdata.network.usa_tamu.model import TAMU
from powersimdata.utility.helpers import MemoryCache, cache_key

_cache = MemoryCache()


class Grid(object):
    """Grid

    :param str/list interconnect: interconnect name(s).
    :param str source: model used to build the network.
    :param str engine: engine used to run scenario, if using ScenarioGrid.
    :raises TypeError: if source and engine are not both strings.
    :raises ValueError: if model or engine does not exist.
    """

    def __init__(self, interconnect, source="usa_tamu", engine="REISE"):
        """Constructor."""
        if not isinstance(source, str):
            raise TypeError("source must be a string")
        supported_engines = {"REISE", "REISE.jl"}
        if engine not in supported_engines:
            raise ValueError(f"Engine must be one of {','.join(supported_engines)}")

        if isinstance(interconnect, str):
            interconnect = [interconnect]
        if not isinstance(interconnect, list):
            raise TypeError("interconnect must be a str of list of str")
        key = cache_key(interconnect, source)
        cached = _cache.get(key)
        if cached is not None:
            data = cached
        elif source == "usa_tamu":
            data = TAMU(interconnect)
        elif os.path.splitext(source)[1] == ".mat":
            if engine == "REISE":
                data = FromREISE(source)
            elif engine == "REISE.jl":
                data = FromREISEjl(source)
        else:
            raise ValueError("%s not implemented" % source)

        self.data_loc = data.data_loc
        self.interconnect = data.interconnect
        self.zone2id = data.zone2id
        self.id2zone = data.id2zone
        self.sub = data.sub
        self.plant = data.plant
        self.gencost = data.gencost
        self.dcline = data.dcline
        self.bus2sub = data.bus2sub
        self.bus = data.bus
        self.branch = data.branch
        self.storage = data.storage

        _cache.put(key, self)

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
        ignored_subkeys = {"gencost"} | set(tamu_storage.defaults.keys())
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
