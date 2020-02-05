import numpy as np
import pandas as pd
import pytest

from powersimdata.input.usa_tamu_model import check_interconnect
from powersimdata.input.helpers import add_column_to_data_frame
from powersimdata.input.mat_reader import format_gencost


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
    add_column_to_data_frame(df, column_to_add)
    assert len(df.columns) == 4
    assert np.array_equal(df.c.values, [True, True, False])


def test_format_gencost_polynomial_only_same_n():
    df_input = pd.DataFrame({0: [2, 2, 2],
                             1: [0.0, 0.0, 0.0],
                             2: [0.0, 0.0, 0.0],
                             3: [4, 4, 4],
                             4: [1.1, 1.2, 1.3],
                             5: [2.7] * 3,
                             6: [0.1, 0.2, 0.3],
                             7: [1.0, 1.0, 2.0]}, index=[1, 2, 3])
    df_output = format_gencost(df_input)
    assert np.array_equal(df_output.columns,
                          ['type', 'startup', 'shutdown', 'n', 'c3', 'c2',
                           'c1', 'c0'])
    assert np.array_equal(df_output.loc[1, ['c0', 'c1', 'c2', 'c3']].values,
                          [1.0, 0.1, 2.7, 1.1])


def test_format_gencost_polynomial_only_different_n():
    df_input = pd.DataFrame({0: [2, 2, 2, 2],
                             1: [0.0, 0.0, 0.0, 0.0],
                             2: [0.0, 0.0, 0.0, 0.0],
                             3: [4, 2, 3, 2],
                             4: [1.1, 0.2, 1.1, 0.4],
                             5: [2.7, 1.0, 0.3, 1.0],
                             6: [0.1, 0.0, 2.0, 0.0],
                             7: [1.0, 0.0, 0.0, 0.0]}, index=[1, 2, 3, 4])
    df_output = format_gencost(df_input)
    assert np.array_equal(df_output.columns,
                          ['type', 'startup', 'shutdown', 'n', 'c3', 'c2',
                           'c1', 'c0'])
    assert np.array_equal(df_output.loc[1, ['c0', 'c1', 'c2', 'c3']].values,
                          [1.0, 0.1, 2.7, 1.1])
    assert np.array_equal(df_output.loc[2, ['c0', 'c1', 'c2', 'c3']].values,
                          [1.0, 0.2, 0.0, 0.0])
    assert np.array_equal(df_output.loc[3, ['c0', 'c1', 'c2', 'c3']].values,
                          [2.0, 0.3, 1.1, 0.0])
    assert np.array_equal(df_output.loc[4, ['c0', 'c1', 'c2', 'c3']].values,
                          [1.0, 0.4, 0.0, 0.0])


def test_format_gencost_piece_wise_linear_only_same_n():
    df_input = pd.DataFrame({0: [1, 1, 1],
                             1: [0.0, 0.0, 0.0],
                             2: [0.0, 0.0, 0.0],
                             3: [3, 3, 3],
                             4: [1.0, 2.0, 3.0],
                             5: [2.7, 2.1, 2.5],
                             6: [2.0, 3.0, 4.0],
                             7: [4.8, 5.4, 7.3],
                             8: [3.0, 4.0, 5.0],
                             9: [10.6, 9.4, 17.7]}, index=[1, 2, 3])
    df_output = format_gencost(df_input)
    assert np.array_equal(df_output.columns,
                          ['type', 'startup', 'shutdown', 'n', 'p1', 'f1',
                           'p2', 'f2', 'p3', 'f3'])


def test_format_gencost_piece_wise_linear_only_different_n():
    df_input = pd.DataFrame({0: [1, 1, 1],
                             1: [0.0, 0.0, 0.0],
                             2: [0.0, 0.0, 0.0],
                             3: [4, 3, 2],
                             4: [1.0, 2.0, 3.0],
                             5: [2.7, 2.1, 2.5],
                             6: [2.0, 3.0, 4.0],
                             7: [4.8, 5.4, 7.3],
                             8: [3.0, 4.0, 0.0],
                             9: [10.6, 9.4, 0.0],
                             10: [4.0, 0.0, 0.0],
                             11: [15.1, 0.0, 0.0]}, index=[1, 2, 3])
    df_output = format_gencost(df_input)
    assert np.array_equal(df_output.columns,
                          ['type', 'startup', 'shutdown', 'n', 'p1', 'f1',
                           'p2', 'f2', 'p3', 'f3', 'p4', 'f4'])
    assert np.array_equal(df_output.loc[1, ['p1', 'f1', 'p2', 'f2', 'p3', 'f3',
                                            'p4', 'f4']].values,
                          [1.0, 2.7, 2.0, 4.8, 3.0, 10.6, 4.0, 15.1])
    assert np.array_equal(df_output.loc[2, ['p1', 'f1', 'p2', 'f2', 'p3', 'f3',
                                            'p4', 'f4']].values,
                          [2.0, 2.1, 3.0, 5.4, 4.0, 9.4, 0.0, 0.0])
    assert np.array_equal(df_output.loc[3, ['p1', 'f1', 'p2', 'f2', 'p3', 'f3',
                                            'p4', 'f4']].values,
                          [3.0, 2.5, 4.0, 7.3, 0.0, 0.0, 0.0, 0.0])


def test_format_gencost_both_model_same_n():
    df_input = pd.DataFrame({0: [1, 2, 1, 2, 2],
                             1: [0.0, 0.0, 0.0, 0.0, 0.0],
                             2: [0.0, 0.0, 0.0, 0.0, 0.0],
                             3: [4, 3, 2, 5, 2],
                             4: [1.0, 1.3, 2.0, 2.8, 1.1],
                             5: [2.7, 2.1, 2.5, 4.5, 6.4],
                             6: [2.0, 3.8, 3.0, 7.3, 0.0],
                             7: [4.8, 0.0, 7.3, 10.0, 0.0],
                             8: [3.0, 0.0, 0.0, 14.3, 0.0],
                             9: [10.6, 0.0, 0.0, 0.0, 0.0],
                             10: [4.0, 0.0, 0.0, 0.0, 0.0],
                             11: [15.1, 0.0, 0.0, 0.0, 0.0]},
                            index=[1, 2, 3, 4, 5])
    df_output = format_gencost(df_input)
    assert np.array_equal(
        df_output.columns,
        ['type', 'startup', 'shutdown', 'n', 'c4', 'c3', 'c2', 'c1', 'c0', 'p1',
         'f1', 'p2', 'f2', 'p3', 'f3', 'p4', 'f4'])
    #assert np.array_equal(df_output.loc[1, ['p1', 'f1', 'p2', 'f2', 'p3', 'f3',
    #                                        'p4', 'f4']].values,
    #                      [1.0, 2.7, 2.0, 4.8, 3.0, 10.6, 4.0, 15.1])
    #assert np.array_equal(df_output.loc[2, ['p1', 'f1', 'p2', 'f2', 'p3', 'f3',
    #                                        'p4', 'f4']].values,
    #                      [2.0, 2.1, 3.0, 5.4, 4.0, 9.4, 0.0, 0.0])
    #assert np.array_equal(df_output.loc[3, ['p1', 'f1', 'p2', 'f2', 'p3', 'f3',
    #                                        'p4', 'f4']].values,
    #                      [3.0, 2.5, 4.0, 7.3, 0.0, 0.0, 0.0, 0.0])

df_input = pd.DataFrame({0: [1, 2, 1, 2, 2],
                         1: [0.0, 0.0, 0.0, 0.0, 0.0],
                         2: [0.0, 0.0, 0.0, 0.0, 0.0],
                         3: [4, 3, 2, 5, 2],
                         4: [1.0, 1.3, 2.0, 2.8, 1.1],
                         5: [2.7, 2.1, 2.5, 4.5, 6.4],
                         6: [2.0, 3.8, 3.0, 7.3, 0.0],
                         7: [4.8, 0.0, 7.3, 10.0, 0.0],
                         8: [3.0, 0.0, 0.0, 14.3, 0.0],
                         9: [10.6, 0.0, 0.0, 0.0, 0.0],
                         10: [4.0, 0.0, 0.0, 0.0, 0.0],
                         11: [15.1, 0.0, 0.0, 0.0, 0.0]},
                        index=[1, 2, 3, 4, 5])