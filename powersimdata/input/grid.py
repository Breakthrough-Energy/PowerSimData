import os

from powersimdata.input.usa_tamu_model import TAMU
from powersimdata.input.scenario_grid import FromREISE, FromREISEjl
from pandas.testing import assert_frame_equal


class Grid(object):
    """Grid
    """
    def __init__(self, interconnect, source='usa_tamu', engine='REISE'):
        """Constructor
        :param list interconnect: interconnect name(s).
        :param str source: model used to build the network.
        :param str engine: engine used to run scenario, if using ScenarioGrid.
        :raises TypeError: if source and engine are not both strings.
        :raises ValueError: if model or engine does not exist.
        """
        if not isinstance(source, str):
            raise TypeError('source must be a string')
        if not isinstance(engine, str):
            got_type = type(engine).__name__
            raise TypeError('engine must be a str, instead got %s' % got_type)

        if source == 'usa_tamu':
            data = TAMU(interconnect)
        elif os.path.splitext(source)[1] == '.mat':
            if engine == 'REISE':
                data = FromREISE(source)
            elif engine == 'REISE.jl':
                data = FromREISEjl(source)
            else:
                raise ValueError('Unknown engine %s!' % engine)

        else:
            raise ValueError('%s not implemented' % source)

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
        self.type2color = get_type2color()
        self.id2type = get_id2type()
        self.type2id = {value: key for key, value in self.id2type.items()}

    def __eq__(self, other):
        """Used when 'self == other' is evaluated.
        :param object other: other object to be compared against.
        :return: (*bool*).
        """

        def _univ_eq(ref, test):
            """Check for {boolean, dataframe, or column data} equality.
            :param object ref: one object to be tested (order does not matter).
            :param object test: another object to be tested.
            :raises AssertionError: if no equality can be confirmed.
            """
            try:
                test_eq = ref == test
                if isinstance(test_eq, (bool, dict)):
                    assert test_eq
                else:
                    assert test_eq.all().all()
            except ValueError:
                assert set(ref.columns) == set(test.columns)
                for col in ref.columns:
                    assert (ref[col] == test[col]).all()

        if not isinstance(other, Grid):
            err_msg = 'Unable to compare Grid & %s' % type(other).__name__
            raise NotImplementedError(err_msg)

        try:
            # compare gencost
            # Comparing 'after' will fail if one Grid was linearized
            self_data = self.gencost['before']
            other_data = other.gencost['before']
            _univ_eq(self_data, other_data)

            # compare storage
            self_storage_num = len(self.storage['gencost'])
            other_storage_num = len(other.storage['gencost'])
            if self_storage_num == 0:
                assert other_storage_num == 0
            else:
                # These are dicts, so we need to go one level deeper
                self_keys = self.storage.keys()
                other_keys = other.storage.keys()
                assert self_keys == other_keys
                for subkey in self_keys:
                    # REISE will modify gencost and some gen columns
                    if subkey != 'gencost':
                        self_data = self.storage[subkey]
                        other_data = other.storage[subkey]
                        if subkey == 'gen':
                            excluded_cols = ['ramp_10', 'ramp_30']
                            self_data = self_data.drop(excluded_cols, axis=1)
                            other_data = other_data.drop(excluded_cols, axis=1)
                        _univ_eq(self_data, other_data)

            # compare bus
            # MOST changes BUS_TYPE for buses with DC Lines attached
            self_df = self.bus.drop('type', axis=1)
            other_df = other.bus.drop('type', axis=1)
            _univ_eq(self_df, other_df)

            # compare plant
            # REISE does some modifications to Plant data
            excluded_cols = ['status', 'Pmin', 'ramp_10', 'ramp_30']
            self_df = self.plant.drop(excluded_cols, axis=1)
            other_df = other.plant.drop(excluded_cols, axis=1)
            _univ_eq(self_df, other_df)

            # check grid helper function equality
            _univ_eq(self.type2color, other.type2color)
            _univ_eq(self.id2type, other.id2type)
            _univ_eq(self.type2id, other.type2id)
            _univ_eq(self.zone2id, other.zone2id)
            _univ_eq(self.id2zone, other.id2zone)
            _univ_eq(self.bus2sub, other.bus2sub)

        except:
            return False
        return True


def get_type2color():
    """Defines generator type to generator color mapping. Used for plotting.
    :return: (*dict*) -- generator type to color mapping.
    """
    type2color = {
        'wind': "xkcd:green",
        'solar': "xkcd:amber",
        'hydro': "xkcd:light blue",
        'ng': "xkcd:orchid",
        'nuclear': "xkcd:silver",
        'coal': "xkcd:light brown",
        'geothermal': "xkcd:hot pink",
        'dfo': "xkcd:royal blue",
        'biomass': "xkcd:dark green",
        'other': "xkcd:melon",
        'storage': "xkcd:orange",
        'wind_offshore': "xkcd:teal",
        }
    return type2color


def get_id2type():
    """Defines generator type to generator id mapping.
    :return: (*tuple*) -- generator type to generator id mapping.
    """
    id2type = {
        0: 'wind',
        1: 'solar',
        2: 'hydro',
        3: 'ng',
        4: 'nuclear',
        5: 'coal',
        6: 'geothermal',
        7: 'dfo',
        8: 'biomass',
        9: 'other',
        10: 'storage',
        11: 'wind_offshore',
        }
    return id2type
