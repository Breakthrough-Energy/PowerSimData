import pandas as pd

# The index name of each dataframe attribute
indices = {
    'branch': 'branch_id',
    'bus': 'bus_id',
    'dcline': 'dcline_id',
    'gencost': 'plant_id',
    'plant': 'plant_id',
    }

# The column names of each dataframe attribute
branch_columns = [
    'from_bus_id', 'to_bus_id', 'r', 'x', 'b', 'rateA', 'rateB', 'rateC',
    'ratio', 'angle', 'status', 'angmin', 'angmax', 'Pf', 'Qf', 'Pt', 'Qt',
    'mu_Sf', 'mu_St', 'mu_angmin', 'mu_angmax', 'branch_device_type',
    'interconnect', 'from_lat', 'from_lon', 'to_lat', 'to_lon',
    'from_zone_id', 'to_zone_id', 'from_zone_name', 'to_zone_name']

bus_columns = [
    'type', 'Pd', 'Qd', 'Gs', 'Bs', 'zone_id', 'Vm', 'Va', 'baseKV', 'Vmax',
    'Vmin', 'lam_P', 'lam_Q', 'mu_Vmax', 'mu_Vmin', 'interconnect', 'lat',
    'lon']

dcline_columns = [
    'from_bus_id', 'to_bus_id', 'status', 'Pf', 'Pt', 'Qf', 'Qt', 'Vf', 'Vt',
    'Pmin', 'Pmax', 'QminF', 'QmaxF', 'QminT', 'QmaxT', 'loss0', 'loss1',
    'muPmin', 'muPmax', 'muQminF', 'muQmaxF', 'muQminT', 'muQmaxT',
    'from_interconnect', 'to_interconnect']

gencost_columns = [
    'type', 'startup', 'shutdown', 'n', 'c2', 'c1', 'c0', 'interconnect']

plant_columns = [
    'bus_id', 'Pg', 'Qg', 'Qmax', 'Qmin', 'Vg', 'mBase', 'status', 'Pmax', 
    'Pmin', 'Pc1', 'Pc2', 'Qc1min', 'Qc1max', 'Qc2min', 'Qc2max', 'ramp_agc',
    'ramp_10', 'ramp_30', 'ramp_q', 'apf', 'mu_Pmax', 'mu_Pmin', 'mu_Qmax',
    'mu_Qmin', 'GenMWMax', 'GenMWMin', 'GenFuelCost', 'GenIOB', 'GenIOC',
    'GenIOD', 'type', 'interconnect', 'lat', 'lon', 'zone_id', 'zone_name']

class MockGrid:
    def __init__(self, grid_attrs):
        """ Constructor.

        :param list grid_attrs: dict of {fieldname, data_dict} pairs.
        """

        if not isinstance(grid_attrs, dict):
            raise TypeError('grid_attrs must be a dict')

        for key in grid_attrs.keys():
            if not isinstance(key, str):
                raise TypeError('grid_attrs keys must all be str')

        extra_keys = set(grid_attrs.keys()) - set(indices.keys())
        if len(extra_keys) > 0:
            raise ValueError('Got unknown key(s):' + str(extra_keys))

        cols = {
            'branch': branch_columns,
            'bus': bus_columns,
            'dcline': dcline_columns,
            'gencost': gencost_columns,
            'plant': plant_columns,
            }

        # Loop through names for grid dataframes, add (maybe empty) dataframes.
        for df_name in indices:
            if df_name in grid_attrs:
                df = pd.DataFrame(grid_attrs[df_name])
            else:
                df = pd.DataFrame(columns=([indices[df_name]]+cols[df_name]))
            df.set_index(indices[df_name], inplace=True)
            setattr(self, df_name, df)

class MockScenario:
    def __init__(self, grid_attrs, pg):
        """ Constructor.

        :param list grid_attrs: fields to be added to grid.
        :param pandas.DataFrame pg: dummy pg
        """
        self.grid_attrs = grid_attrs
        self.pg = pg

    def get_grid(self):
        """Get grid

        :return: (GridMock) -- mock grid
        """
        return MockGrid(self.grid_attrs)

    def get_pg(self):
        return self.pg
