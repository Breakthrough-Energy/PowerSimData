import numpy as np
import pandas as pd
import pytest

from powersimdata.input.usa_tamu_model import check_interconnect
from powersimdata.input.helpers import add_column_to_data_frame


def test_interconnect_type():
    interconnect = 'Western'
    with pytest.raises(TypeError):
        check_interconnect(interconnect)


def test_interconnect_value():
    interconnect = ['Canada']
    with pytest.raises(ValueError):
        check_interconnect(interconnect)


def test_interconnect_duplicate_value():
    interconnect = ['Western', 'Western', 'Texas']
    with pytest.raises(ValueError,
                       match='List of interconnects contains duplicate values'):
        check_interconnect(interconnect)


def test_interconnect_usa_is_unique():
    interconnect = ['Western', 'USA']
    with pytest.raises(ValueError, match='USA interconnect cannot be paired'):
        check_interconnect(interconnect)


def test_add_column_to_data_frame():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    column_to_add = {'c': [True, True, False], 'd': ['one', 2, 'three']}
    df = add_column_to_data_frame(df, column_to_add)
    assert len(df.columns) == 4
    assert np.array_equal(df.c.values, [True, True, False])
