import pandas as pd

from powersimdata.scenario.analyze import Analyze
from powersimdata.tests.mock_grid import MockGrid


def _ensure_ts_index(df):
    """If a dataframe is provided and the index is not a time series, add a time series
    index. If the input is None, return it as is.

    :param pandas.DataFrame/None df: data frame, or None.
    :return: (*pandas.DataFrame/None*) -- input, with time series index if possible.
    """
    if df is None:
        return df
    if not isinstance(df.index, pd.DatetimeIndex):
        df.set_index(
            pd.date_range(start="2016-01-01", periods=len(df), freq="H"),
            inplace=True,
        )
        df.index.name = "UTC"
    return df


class MockAnalyze:
    def __init__(
        self,
        grid_attrs=None,
        congl=None,
        congu=None,
        ct=None,
        demand=None,
        lmp=None,
        pg=None,
        storage_pg=None,
        solar=None,
        wind=None,
        hydro=None,
    ):
        """Constructor.

        :param dict grid_attrs: fields to be added to grid.
        :param pandas.DataFrame congl: dummy congl
        :param pandas.DataFrame congu: dummy congu
        :param dict ct: dummy ct
        :param pandas.DataFrame demand: dummy demand
        :param pandas.DataFrame lmp: dummy lmp
        :param pandas.DataFrame pg: dummy pg
        :param pandas.DataFrame storage_pg: dummy storage_pg
        :param pandas.DataFrame solar: dummy solar
        :param pandas.DataFrame wind: dummy wind
        :param pandas.DataFrame hydro: dummy hydro
        """
        self.grid = MockGrid(grid_attrs)
        self.congl = _ensure_ts_index(congl)
        self.congu = _ensure_ts_index(congu)
        self.ct = ct if ct is not None else {}
        self.demand = _ensure_ts_index(demand)
        self.lmp = _ensure_ts_index(lmp)
        self.pg = _ensure_ts_index(pg)
        self.storage_pg = _ensure_ts_index(storage_pg)
        self.solar = _ensure_ts_index(solar)
        self.wind = _ensure_ts_index(wind)
        self.hydro = _ensure_ts_index(hydro)
        self.name = "analyze"

    def get_congl(self):
        """Get congl.
        :return: (pandas.DataFrame) -- dummy congl
        """
        return self.congl

    def get_congu(self):
        """Get congu.
        :return: (pandas.DataFrame) -- dummy congu
        """
        return self.congu

    def get_ct(self):
        """Get ct.
        :return: (Dict) -- dummy ct
        """
        return self.ct

    def get_demand(self, original=None):
        """Get demand.
        :return: (pandas.DataFrame) -- dummy demand
        """
        return self.demand

    def get_grid(self):
        """Get grid.
        :return: (MockGrid) -- mock grid
        """
        return self.grid

    def get_lmp(self):
        """Get lmp.
        :return: (pandas.DataFrame) -- dummy lmp
        """
        return self.lmp

    def get_pg(self):
        """Get PG.
        :return: (pandas.DataFrame) -- dummy pg
        """
        return self.pg

    def get_storage_pg(self):
        """Get storage PG.
        :return: (pandas.DataFrame) -- dummy storage_pg
        """
        return self.storage_pg

    def get_solar(self):
        """Get solar.
        :return: (pandas.DataFrame) -- dummy solar
        """
        return self.solar

    def get_wind(self):
        """Get wind.
        :return: (pandas.DataFrame) -- dummy wind
        """
        return self.wind

    def get_hydro(self):
        """Get hydro.
        :return: (pandas.DataFrame) -- dummy hydro
        """
        return self.hydro

    @property
    def __class__(self):
        """If anyone asks, I'm an Analyze object!"""
        return Analyze
