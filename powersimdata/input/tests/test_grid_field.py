from powersimdata.input.grid_fields import HierarchicalGridField
import pytest
import pandas as pd
import unittest
from pandas.testing import assert_frame_equal


def test_change_table_parsing():
    input_ct = {'wind': {301: 3}, 'coal': {302: 5, 304: 6, 305: 10}}
    change_table_hierarchy = ['type', 'zoneid']
    result = HierarchicalGridField.ct_hierarchy_iterator(input_ct, change_table_hierarchy)

    # Answer should be:
    # [{'ct_hierarchy': ['type', 'zoneid'], 'index': ('wind', 301), 'scaling_value': 3},
    #  {'ct_hierarchy': ['type', 'zoneid'], 'index': ('coal', 302), 'scaling_value': 5},
    #  {'ct_hierarchy': ['type', 'zoneid'], 'index': ('coal', 304), 'scaling_value': 6},
    #  {'ct_hierarchy': ['type', 'zoneid'], 'index': ('coal', 305), 'scaling_value': 10}]

    for change in result:
        change['ct_hierarchy'] == change_table_hierarchy
        len(change['ct_hierarchy']) == len(change['index']) == 2
        assert input_ct[change['index'][0]][change['index'][1]] == change['scaling_value']


def test_change_table_error():
    input_ct = {'wind': {301: 3}, 'coal': {302: [5], 304: 6, 305: 10}}
    change_table_hierarchy = ['type', 'zoneid']
    with pytest.raises(KeyError):
        list(HierarchicalGridField.ct_hierarchy_iterator(input_ct, change_table_hierarchy))


def test_change_table_depth_mixed_type():
    input_ct = {'wind': {3}, 'coal': {302: [5], 304: 6, 305: 10}}
    change_table_hierarchy = ['type', 'zoneid']
    with pytest.raises(KeyError):
        list(HierarchicalGridField.ct_hierarchy_iterator(input_ct, change_table_hierarchy))


def test_change_table_depth_too_shallow():
    input_ct = {'wind': 3, 'coal': {302: 5, 304: 6, 305: 10}}
    change_table_hierarchy = ['type', 'zoneid']
    with pytest.raises(AssertionError):
        list(HierarchicalGridField.ct_hierarchy_iterator(input_ct, change_table_hierarchy))


def test_change_table_depth_too_deep():
    input_ct = {'wind': {301: {301: 3}}, 'coal': {302: 5, 304: 6, 305: 10}}
    change_table_hierarchy = ['type', 'zoneid']
    with pytest.raises(AssertionError):
        list(HierarchicalGridField.ct_hierarchy_iterator(input_ct, change_table_hierarchy))


# For these tests, the grouping are as follows:
#
# type   zone_name
# hydro  Atlantic     103
#        Pacific      106
# solar  Pacific      101
#        Pacific      104
#        Pacific      105
# wind   Atlantic     102
# Name: plant_id, dtype: int64


def test_single_group_index():
    plant = _create_grid_plant_dataframe()
    plant_field = HierarchicalGridField(plant, 'plant', {})

    type_zone_index = plant_field.get_hierarchical_grouping(['type', 'zone_name'])
    idx = type_zone_index.get_idx(('solar', 'Pacific'))

    tc = unittest.TestCase('__init__')
    tc.assertEqual(idx, [101, 104, 105])

    assert_frame_equal(plant.loc[idx], plant.loc[[101, 104, 105]])


def test_single_hierarchical_index():
    plant = _create_grid_plant_dataframe()
    plant_field = HierarchicalGridField(plant, 'plant', {})

    type_zone_index = plant_field.get_hierarchical_index(['type', 'zone_name'])
    idx = type_zone_index.get_idx(('solar', 'Pacific'))

    tc = unittest.TestCase('__init__')
    tc.assertEqual(idx, [101, 104, 105])

    assert_frame_equal(plant.loc[idx], plant.loc[[101, 104, 105]])


def test_multiple_hierarchical_index():
    plant = _create_grid_plant_dataframe()
    plant_field = HierarchicalGridField(plant, 'plant', {})

    type_zone_index = plant_field.get_hierarchical_index(['type', 'zone_name'])
    idx = type_zone_index.get_idx((['solar', 'wind'], ['Atlantic', 'Pacific']))

    tc = unittest.TestCase('__init__')
    tc.assertEqual(idx, [101, 104, 105, 102])

    assert_frame_equal(plant.loc[idx], plant.loc[[101, 104, 105, 102]])


def _create_grid_plant_dataframe():
    mock_plant = {
        'plant_id': [101, 102, 103, 104, 105, 106],
        'bus_id': [1001, 1002, 1003, 1004, 1005, 1006],
        'type': ['solar', 'wind', 'hydro', 'solar', 'solar', 'hydro'],
        'zone_name': ['Pacific', 'Atlantic', 'Atlantic', 'Pacific',
                      'Pacific', 'Pacific'],
        'GenFuelCost': [0, 0, 3.3, 4.4, 5.5, 0],
        'Pmax': [50, 200, 80, 100, 120, 220],
    }
    plant = pd.DataFrame(mock_plant)
    plant.set_index('plant_id', inplace=True)
    return plant
