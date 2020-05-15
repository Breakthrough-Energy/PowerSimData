import numpy as np
import pandas as pd
import pytest
import unittest
import copy

from powersimdata.input.usa_tamu_model import check_interconnect
from powersimdata.input.helpers import add_column_to_data_frame
from powersimdata.input.scenario_grid import format_gencost, link
from powersimdata.input.grid import Grid
from powersimdata.input.usa_tamu_model import TAMU


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


def test_grid_type():
    g = Grid(['USA'])
    assert isinstance(g, Grid)


def test_drop_one_interconnect():
    model = TAMU(['Western', 'Texas'])
    assert model.interconnect == ['Western', 'Texas']
    assert 'eastern' not in model.sub.interconnect.unique()
    assert 'eastern' not in model.bus2sub.interconnect.unique()
    assert 'eastern' not in model.bus.interconnect.unique()
    assert 'eastern' not in model.plant.interconnect.unique()
    assert 'eastern' not in model.branch.interconnect.unique()
    assert 'eastern' not in model.gencost['before'].interconnect.unique()
    assert 'eastern' not in model.gencost['after'].interconnect.unique()
    assert 'eastern' not in model.dcline.from_interconnect.unique()
    assert 'eastern' not in model.dcline.to_interconnect.unique()


def test_drop_two_interconnect():
    model = TAMU(['Western'])
    assert model.interconnect == ['Western']
    for interconnect in ['Eastern', 'Texas']:
        assert interconnect not in model.sub.interconnect.unique()
        assert interconnect not in model.bus2sub.interconnect.unique()
        assert interconnect not in model.bus.interconnect.unique()
        assert interconnect not in model.plant.interconnect.unique()
        assert interconnect not in model.branch.interconnect.unique()
        assert interconnect not in model.gencost['before'].interconnect.unique()
        assert interconnect not in model.gencost['after'].interconnect.unique()
        assert interconnect not in model.dcline.from_interconnect.unique()
        assert interconnect not in model.dcline.to_interconnect.unique()


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
    assert np.array_equal(
        df_output.loc[1, ['c4', 'c3', 'c2', 'c1', 'c0', 'p1', 'f1', 'p2', 'f2',
                          'p3', 'f3', 'p4', 'f4']].values,
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.7, 2.0, 4.8, 3.0, 10.6, 4.0, 15.1])
    assert np.array_equal(
        df_output.loc[2, ['c4', 'c3', 'c2', 'c1', 'c0', 'p1', 'f1', 'p2', 'f2',
                          'p3', 'f3', 'p4', 'f4']].values,
        [0.0, 0.0, 1.3, 2.1, 3.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert np.array_equal(
        df_output.loc[3, ['c4', 'c3', 'c2', 'c1', 'c0', 'p1', 'f1', 'p2', 'f2',
                          'p3', 'f3', 'p4', 'f4']].values,
        [0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 2.5, 3.0, 7.3, 0.0, 0.0, 0.0, 0.0])
    assert np.array_equal(
        df_output.loc[4, ['c4', 'c3', 'c2', 'c1', 'c0', 'p1', 'f1', 'p2', 'f2',
                          'p3', 'f3', 'p4', 'f4']].values,
        [2.8, 4.5, 7.3, 10.0, 14.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert np.array_equal(
        df_output.loc[5, ['c4', 'c3', 'c2', 'c1', 'c0', 'p1', 'f1', 'p2', 'f2',
                          'p3', 'f3', 'p4', 'f4']].values,
        [0.0, 0.0, 0.0, 1.1, 6.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])


def test_link():
    keys = ['a', 'b', 'c', 'd', 'e']
    values = [1, 2, 3, 4, 5]
    output = link(keys, values)
    assert np.array_equal(list(output.keys()), keys)
    assert np.array_equal(list(output.values()), values)
    assert np.array_equal(output['a'], values[0])
    assert np.array_equal(output['c'], values[2])


@pytest.fixture(scope="session")
def base_texas():
    return Grid(['Texas'])


@pytest.fixture(scope="session")
def base_western():
    return Grid(['Western'])


def test_deepcopy_works(base_texas):
    assert isinstance(copy.deepcopy(base_texas), Grid)


def test_grid_eq_success_simple(base_texas):
    assert base_texas == Grid(['Texas'])


def test_grid_eq_failure_simple(base_texas, base_western):
    assert base_texas != base_western


def test_grid_eq_failure_bus(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.bus.baseKV.iloc[0] *= 2
    assert base_texas != test_grid


def test_grid_eq_success_bus_type(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.bus.type = 1
    assert base_texas == test_grid


def test_grid_eq_failure_branch(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.branch.rateA.iloc[0] *= 2
    assert base_texas != test_grid


def test_grid_eq_failure_dcline(base_western):
    test_grid = copy.deepcopy(base_western)
    test_grid.dcline.Pmax.iloc[0] *= 2
    assert base_western != test_grid


def test_grid_eq_failure_gencost_before(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.gencost['before'].n.iloc[0] += 1
    assert base_texas != test_grid


def test_grid_eq_success_gencost_after(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.gencost['after'] = test_grid.gencost['after'].drop(
        test_grid.gencost['after'].tail(1).index)
    assert base_texas == test_grid


def test_grid_eq_failure_plant(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.plant.Pmax.iloc[0] *= 2
    assert base_texas != test_grid


def test_grid_eq_success_plant_ramp30(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.plant.ramp_30.iloc[0] *= 2
    assert base_texas == test_grid


def test_grid_eq_failure_sub(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.sub.name.iloc[0] = test_grid.sub.name.iloc[0][::-1]
    assert base_texas != test_grid


def test_grid_eq_failure_storage(base_texas):
    test_grid = copy.deepcopy(base_texas)
    gencost = {g: 0 for g in test_grid.storage['gencost'].columns}
    gen = {g: 0 for g in test_grid.storage['gen'].columns}
    test_grid.storage['gencost'] = test_grid.storage['gencost'].append(
        gencost, ignore_index=True)
    test_grid.storage['gen'] = test_grid.storage['gen'].append(
        gen, ignore_index=True)
    assert base_texas != test_grid


def test_that_fields_are_not_modified_when_loading_another_grid():
    western_grid = Grid(['Western'])
    western_plant_original_shape = western_grid.plant.shape
    eastern_grid = Grid(['Eastern'])
    assert western_plant_original_shape == western_grid.plant.shape


def test_that_fields_can_be_modified_with_conventional_syntax():
    grid = Grid(['Texas'])
    grid.plant = grid.plant.append(grid.plant.iloc[0:4])
    assert grid.plant.shape == grid.plant.shape
