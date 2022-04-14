import numpy as np
import pandas as pd

from powersimdata.input.grid import Grid


class MockProfileInput:
    """
    MockInputData is a mock of powersimdata.input.profile_input.ProfileInput
    that generates random profiles.

    Exactly 3 of {`start_time`, `end_time`, `periods`, `freq`} must be specified. See <https://pandas.pydata.org/docs/reference/api/pandas.date_range.html>.

    :param powersimdata.input.grid.Grid grid: instance of Grid object.
    :param str start_time: when profiles begin.
    :param str end_time: when profiles end.
    :param int periods: number of times in profile.
    :param str freq: frequency of times in profile.
    :param int random_seed: used to initialize the random generator.
    :raises ValueError: raised if `field_name` specified in `get_data()` is not specified by this mock
    :return: (*powersimdata.tests.mock_profile_input.MockProfileInput*)
    """

    _RESOURCES = {
        "wind": {"wind", "wind_offshore"},
        "solar": {"solar"},
        "hydro": {"hydro"},
    }

    def __init__(
        self,
        grid: Grid,
        start_time="2016-01-01 00:00:00",
        end_time=None,
        periods=24,
        freq="H",
        random_seed=6669,
    ):
        self._grid = grid
        self._start_time = start_time
        self._end_time = end_time
        self._periods = periods
        self._freq = freq
        self._random = np.random.default_rng(seed=random_seed)

        self._profiles = {
            "demand": self._get_demand(),
            **{
                resource: self._get_resource_profile(resource)
                for resource in self._RESOURCES.keys()
            },
        }
        self._profiles.update(self._get_demand_flexibility())

    def get_data(self, scenario_info, field_name):
        """Returns fake profile data.

        :param dict scenario_info: not used.
        :param str field_name: Can be any of *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
            *'demand_flexibility_up'*, or *'demand_flexibility_dn'*.
        :return: (*pandas.DataFrame*) -- fake profile data
        """
        profile = self._profiles.get(field_name)

        if profile is None:
            raise ValueError(f"No profile specified for {field_name}!")

        return profile

    def _get_demand(self):
        """Returns fake demand data.

        :return: (*pandas.DataFrame*) -- fake demand data
        """
        zone_ids = set(self._grid.plant["zone_id"])
        fake_demand_profile = self._create_fake_profile(zone_ids)
        return fake_demand_profile

    def _get_demand_flexibility(self):
        """Returns fake flexible demand data.

        :return: (*dict*) -- dictionary of fake flexibile demand data
        """
        zone_ids = set(self._grid.plant["zone_id"])
        demand_flexibility_profile_types = [
            "demand_flexibility_up",
            "demand_flexibility_dn",
        ]
        fake_demand_flexibility_profiles = {
            p: self._create_fake_profile(zone_ids, demand_flexibility=True)
            for p in demand_flexibility_profile_types
        }
        return fake_demand_flexibility_profiles

    def _get_resource_profile(self, resource_type):
        """Returns fake data for given resource_type.

        :param str resource_type: Can be any of *'hydro'*, *'solar'*, or *'wind'*.
        :return: (*pandas.DataFrame*) -- fake data for resource
        """
        plant_ids = self._get_plant_ids_for_type(resource_type)
        fake_resource_profile = self._create_fake_profile(plant_ids)
        return fake_resource_profile

    def _get_plant_ids_for_type(self, resource_type):
        """Retrieves plant_ids for plants of `resource_type` from the grid.

        :param str resource_type: Can be any of *'hydro'*, *'solar'*, or *'wind'*.
        :return: (*list*) -- list of plant_ids
        """
        resources = self._RESOURCES[resource_type]
        plant_ids = list(self._grid.plant[lambda ds: ds.type.isin(resources)].index)
        return plant_ids

    def _create_fake_profile(self, columns, demand_flexibility=False):
        """Generates a fake profile.

        :param list columns: columns for the DataFrame
        :param bool demand_flexibility: indicates whether the fake profile being created
            is a demand flexibility profile.
        :return: (*pandas.DataFrame*) -- a fake profile
        """
        times = pd.date_range(
            start=self._start_time,
            end=self._end_time,
            periods=self._periods,
            freq=self._freq,
        )
        index = pd.Index(times, name="UTC Time")
        data = self._random.uniform(low=0, high=1, size=(len(times), len(columns)))
        fake_profile = pd.DataFrame(data=data, index=index, columns=columns)
        if demand_flexibility:
            fake_profile.columns = [f"zone.{z}" for z in columns]
        return fake_profile
