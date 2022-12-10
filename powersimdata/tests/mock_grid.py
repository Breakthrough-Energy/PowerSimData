import pandas as pd

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.const import grid_const
from powersimdata.input.grid import Grid
from powersimdata.network.model import ModelImmutables


class MockGrid(AbstractGrid):
    def __init__(self, grid_attrs=None, model="usa_tamu"):
        """Constructor.

        :param dict grid_attrs: dictionary of {*field_name*, *data_dict*} pairs where
            *field_name* can be: sub, bus2sub, branch, bus, dcline, plant,
            gencost_before, gencost_after, storage_gen, storage_StorageData and
            *data_dict* is a dictionary in which the keys are the column name of the
            data frame associated to *field_name* and the values are a list of values.
        :param str model: grid model. Use to access geographical information such
            as loadzones, interconnections, etc.
        :raises TypeError:
            if ``grid_attrs`` is not a dict.
            if keys of ``grid_attrs`` are not str.
        :raises ValueError: if a key of ``grid_attrs`` is incorrect.
        """
        if grid_attrs is None:
            grid_attrs = {}

        if not isinstance(grid_attrs, dict):
            raise TypeError("grid_attrs must be a dict")

        for key in grid_attrs.keys():
            if not isinstance(key, str):
                raise TypeError("grid_attrs keys must all be str")

        extra_keys = set(grid_attrs) - set(grid_const.indices).union(
            {"gencost_before", "gencost_after", "storage_gen", "storage_StorageData"}
        )
        if len(extra_keys) > 0:
            raise ValueError("Got unknown key(s):" + str(extra_keys))

        super().__init__()
        self.grid_model = model
        self.model_immutables = ModelImmutables(model)

        other = {}
        for k, v in grid_attrs.items():
            if k in grid_const.indices:
                setattr(self, k, pd.DataFrame(v).set_index(grid_const.indices[k]))
            else:
                s = k.split("_")
                df = (
                    pd.DataFrame(v).set_index("plant_id")
                    if s[0] == "gencost"
                    else pd.DataFrame(v)
                )

                if s[0] not in other:
                    other[s[0]] = {s[1]: df}
                else:
                    other[s[0]][s[1]] = df

        for k, v in other.items():
            setattr(self, k, v)

    @property
    def __class__(self):
        """If anyone asks, I'm a Grid object!"""
        return Grid
