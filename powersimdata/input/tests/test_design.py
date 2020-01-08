import unittest

from postreise.tests.mock_grid import MockGrid
from powersimdata.tests.mock_change_table import MockChangeTable
from powersimdata.input.design import (
    _find_branches_connected_to_bus, _find_first_degree_branches,
    _find_stub_degree, _find_capacity_at_bus, scale_renewable_stubs)

"""
This test network is a ring, with several spurs coming off of it. The central
ring is buses {1, 2, 3, 4}, and has three spurs coming off of it:
    bus 2 ----- bus 5 (with a wind generator).
    bus 4 ----- bus 6 ----- bus 7 (with two solar generators and one ng)
    bus 3 ----- bus 8 (with a wind generator)
"""

mock_branch = {
    'branch_id': [101, 102, 103, 104, 105, 106, 107, 108],
    'from_bus_id': [1, 2, 2, 3, 3, 4, 4, 6],
    'to_bus_id': [2, 3, 5, 8, 4, 1, 6, 7],
    'rateA': [100, 100, 8, 25, 100, 100, 15, 25],
    }

mock_bus = {
    'bus_id': [1, 2, 3, 4, 5, 6, 7, 8],
    'zone_id': ['W', 'E', 'E', 'W', 'E', 'W', 'W', 'E'],
    }

mock_plant = {
    'plant_id': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
    'bus_id': [1, 1, 5, 7, 7, 7, 8],
    'type': ['solar', 'coal', 'wind', 'solar', 'solar', 'ng', 'wind'],
    'GenMWMax': [15, 30, 10, 12, 8, 20, 15]
    }

mock_grid = MockGrid(
    grid_attrs={'branch': mock_branch, 'bus': mock_bus, 'plant': mock_plant})


class TestHelpers(unittest.TestCase):
    
    def setUp(self):
        self.branch = mock_grid.branch
        self.plant = mock_grid.plant
    
    def test_find_branches_connected_to_bus_1(self):
        branches_connected = _find_branches_connected_to_bus(self.branch, 1)
        self.assertEqual(branches_connected, {101, 106})
    
    def test_find_branches_connected_to_bus_4(self):
        branches_connected = _find_branches_connected_to_bus(self.branch, 4)
        self.assertEqual(branches_connected, {105, 106, 107})
    
    def test_find_branches_connected_to_bus_5(self):
        branches_connected = _find_branches_connected_to_bus(self.branch, 5)
        self.assertEqual(branches_connected, {103})
    
    def test_find_first_degree_branches_101(self):
        branches_connected = _find_first_degree_branches(self.branch, 101)
        self.assertEqual(branches_connected, {101, 102, 103, 106})
    
    def test_find_first_degree_branches_108(self):
        branches_connected = _find_first_degree_branches(self.branch, 108)
        self.assertEqual(branches_connected, {107, 108})
    
    def test_find_stub_degree_1(self):
        stub_degree, stubs = _find_stub_degree(self.branch, 1)
        self.assertEqual(stub_degree, 0)
        self.assertEqual(stubs, set())
    
    def test_find_stub_degree_5(self):
        stub_degree, stubs = _find_stub_degree(self.branch, 5)
        self.assertEqual(stub_degree, 1)
        self.assertEqual(stubs, {103})
    
    def test_find_stub_degree_7(self):
        stub_degree, stubs = _find_stub_degree(self.branch, 7)
        self.assertEqual(stub_degree, 2)
        self.assertEqual(stubs, {107, 108})
    
    def test_find_capacity_at_bus_1_solar_tuple(self):
        gen_capacity = _find_capacity_at_bus(self.plant, 1, ('solar',))
        self.assertEqual(gen_capacity, 15)
    
    def test_find_capacity_at_bus_1_solar_str(self):
        gen_capacity = _find_capacity_at_bus(self.plant, 1, 'solar')
        self.assertEqual(gen_capacity, 15)
    
    def test_find_capacity_at_bus_2_wind(self):
        gen_capacity = _find_capacity_at_bus(self.plant, 2, ('wind',))
        self.assertEqual(gen_capacity, 0)
    
    def test_find_capacity_at_bus_7_solar(self):
        gen_capacity = _find_capacity_at_bus(self.plant, 7, ('solar',))
        self.assertEqual(gen_capacity, 20)
    
    def test_find_capacity_at_bus_7_solar_ng(self):
        gen_capacity = _find_capacity_at_bus(self.plant, 7, ('solar', 'ng'))
        self.assertEqual(gen_capacity, 40)


class TestScaleRenewableStubs(unittest.TestCase):
    
    def test_empty_ct_inplace_default(self):
        expected_ct = {'branch':{'branch_id':{103: (11/8), 107: (21/15)}}}
        change_table = MockChangeTable(mock_grid)
        returned = scale_renewable_stubs(change_table, verbose=False)
        self.assertIsNone(returned)
        self.assertEqual(change_table.ct, expected_ct)
    
    def test_empty_ct_inplace_true(self):
        expected_ct = {'branch':{'branch_id':{103: (11/8), 107: (21/15)}}}
        change_table = MockChangeTable(mock_grid)
        returned = scale_renewable_stubs(change_table, verbose=False)
        self.assertIsNone(returned)
        self.assertEqual(change_table.ct, expected_ct)
    
    def test_empty_ct_inplace_false(self):
        expected_ct = {'branch':{'branch_id':{103: (11/8), 107: (21/15)}}}
        change_table = MockChangeTable(mock_grid)
        returned = scale_renewable_stubs(
            change_table, inplace=False, verbose=False)
        self.assertEqual(change_table.ct, {})
        self.assertEqual(returned, expected_ct)
    
    def test_empty_ct_no_fuzz(self):
        expected_ct = {'branch':{'branch_id':{103: (10/8), 107: (20/15)}}}
        change_table = MockChangeTable(mock_grid)
        returned = scale_renewable_stubs(change_table, fuzz=0, verbose=False)
        self.assertIsNone(returned)
        self.assertEqual(change_table.ct, expected_ct)
    
    def test_existing_ct_unrelated_branch_id(self):
        ct = {'branch':{'branch_id':{105: 2}}}
        change_table = MockChangeTable(mock_grid, ct=ct)
        expected_ct = {
            'branch':{'branch_id':{103: (11/8), 105:2, 107: (21/15)}}}
        scale_renewable_stubs(change_table, verbose=False)
        self.assertEqual(change_table.ct, expected_ct)
    
    def test_existing_ct_zone_id_wind(self):
        ct = {'wind':{'zone_id':{'E': 2}}}
        change_table = MockChangeTable(mock_grid, ct=ct)
        expected_ct = {
            'wind':{'zone_id':{'E': 2}},
            'branch':{'branch_id':{103: (21/8), 104: (31/25), 107: (21/15)}}
            }
        scale_renewable_stubs(change_table, verbose=False)
        self.assertEqual(change_table.ct, expected_ct)

    def test_existing_ct_zone_id_solar_wind(self):
        ct = {
            'wind':{'zone_id':{'E': 2}},
            'solar':{'zone_id':{'W': 3}},
            }
        change_table = MockChangeTable(mock_grid, ct=ct)
        expected_ct = {
            'wind':{'zone_id':{'E': 2}},
            'solar':{'zone_id':{'W': 3}},
            'branch':{'branch_id':{
                103: (21/8), 104: (31/25), 107: (61/15), 108: (61/25)}},
            }
        scale_renewable_stubs(change_table, verbose=False)
        self.assertEqual(change_table.ct, expected_ct)