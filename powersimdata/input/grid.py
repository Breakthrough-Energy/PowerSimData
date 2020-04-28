import os
import warnings

from powersimdata.input.usa_tamu_model import TAMU
from powersimdata.input.scenario_grid import FromREISE, FromREISEjl
from powersimdata.input.grid_fields \
    import AbstractGridField, Branch, Bus, DCLine, GenCost, Plant, Storage, Sub


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

        # Specific grid info
        self.data_loc = data.data_loc
        self.interconnect = data.interconnect

        self.fields = {}
        self.transform = {}

        # Input data as grid fields
        self.fields['bus'] = Bus(data.bus)
        self.fields['branch'] = Branch(data.branch)
        self.fields['dcline'] = DCLine(data.dcline)
        self.fields['gencost'] = GenCost(data.gencost)
        self.fields['plant'] = Plant(data.plant)
        self.fields['sub'] = Sub(data.sub)
        self.fields['storage'] = Storage(data.storage)

        # Conversion helpers
        self.transform['bus2sub'] = data.bus2sub
        self.transform['zone2id'] = data.zone2id
        self.transform['id2zone'] = data.id2zone
        self.transform['id2type'] = get_id2type()
        self.transform['type2id'] = {value: key for key, value in
                                     self.transform['id2type'].items()}

        # Plotting helper
        self.transform['type2color'] = get_type2color()

    def __getattr__(self, prop_name):
        """
        Overrides the object "." property interface to maintain backwards
        compatibility, i.e. grid.plant
        is the same as grid.fields["plant"], or grid.transform["bus2sub"]

        :param str prop_name: property name as string
        :raises KeyError: For attempts to use key not in the dictionary
        :return: property of the Grid class
        """

        # needed for deepcopy to work
        if prop_name == "__deepcopy__":
            return super().__deepcopy__
        if prop_name == "__len__":
            return super().__len__
        if prop_name == "__getstate__":
            return super().__getstate__
        if prop_name == "__setstate__":
            return super().__setstate__

        # switch between transform and grid_field attributes
        if prop_name in ['bus2sub', 'zone2id', 'id2zone', 'id2type', 
                         'type2id', 'type2color']:
            return self.transform[prop_name]
        else:
            try:
                warnings.warn(
                    "Grid property access is moving to dictionary indexing, "
                    "i.e. grid['branch'] consistent with REISE.jl",
                    DeprecationWarning
                )
                return self.fields[prop_name].data
            except AttributeError as e:
                print(e)

    def __getitem__(self, field_name):
        """
        Allows indexing into the resources dictionary directly from the
        object variable, i.e. grid["plant"] is the
        same as grid.fields["plant"]
        :param str field_name: grid field name as string
        :raises KeyError: For attempts to use key not in the dictionary
        :return: property of the Grid class
        """
        try:
            return self.fields[field_name].data
        except KeyError as e:
            print(e)

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
        assert self.fields.keys() == other.fields.keys()
        assert self.transform.keys() == other.transform.keys()
        # Check all AbstractGridField attributes
        try:
            for k, v in self.fields.items():
                if isinstance(v, GenCost):
                    # Comparing 'after' will fail if one Grid was linearized
                    self_data = self.fields[k].data['before']
                    other_data = other.fields[k].data['before']
                    _univ_eq(self_data, other_data)
                elif isinstance(v, Storage):
                    self_storage_num = len(self.fields[k].data['gencost'])
                    other_storage_num = len(other.fields[k].data['gencost'])
                    if self_storage_num == 0:
                        assert other_storage_num == 0
                        continue
                    # These are dicts, so we need to go one level deeper
                    self_keys = self.fields[k].data.keys()
                    other_keys = other.fields[k].data.keys()
                    assert self_keys == other_keys
                    for subkey in self_keys:
                        # REISE will modify gencost and some gen columns
                        if subkey == 'gencost':
                            continue
                        self_data = self.fields[k].data[subkey]
                        other_data = other.fields[k].data[subkey]
                        if subkey == 'gen':
                            excluded_cols = ['ramp_10', 'ramp_30']
                            self_data = self_data.drop(excluded_cols, axis=1)
                            other_data = other_data.drop(excluded_cols, axis=1)
                        _univ_eq(self_data, other_data)
                elif isinstance(v, Bus):
                    # MOST changes BUS_TYPE for buses with DC Lines attached
                    self_df = self.fields[k].data.drop('type', axis=1)
                    other_df = other.fields[k].data.drop('type', axis=1)
                    _univ_eq(self_df, other_df)
                elif isinstance(v, Plant):
                    # REISE does some modifications to Plant data
                    excluded_cols = ['status', 'Pmin', 'ramp_10', 'ramp_30']
                    self_df = self.fields[k].data.drop(excluded_cols, axis=1)
                    other_df = other.fields[k].data.drop(excluded_cols, axis=1)
                    _univ_eq(self_df, other_df)
                elif isinstance(v, AbstractGridField):
                    _univ_eq(self.fields[k].data, other.fields[k].data)
                else:
                    _univ_eq(self.fields[k], other.fields[k])
            # Check the transform attributes
            for k, v in self.transform.items():
                _univ_eq(self.transform[k], other.transform[k])
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
