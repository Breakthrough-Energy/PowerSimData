import unittest

import numpy as np
import pandas as pd

from powersimdata.tests.mock_grid import MockGrid
from powersimdata.tests.mock_scenario import MockScenario
from powersimdata.tests.mock_change_table import MockChangeTable
from powersimdata.design.transmission import (
    _find_branches_connected_to_bus, _find_first_degree_branches,
    _find_stub_degree, _find_capacity_at_bus, scale_renewable_stubs,
    _identify_mesh_branch_upgrades, _construct_composite_allow_list,
    _increment_branch_scaling)

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
    'rateA': [0.25, 1, 8, 25, 100, 100, 15, 25],
    'from_lat': [47, 47, 47, 46, 46, 46, 46, 46],
    'from_lon': [122, 122, 122, 122, 122, 123, 123, 124],
    'to_lat': [47, 46, 47, 46, 46, 47, 46, 46],
    'to_lon': [122, 122, 112, 121, 123, 122, 124, 125],
    }

mock_bus = {
    'bus_id': [1, 2, 3, 4, 5, 6, 7, 8],
    'zone_id': ['W', 'E', 'E', 'W', 'E', 'W', 'W', 'E'],
    }

mock_plant = {
    'plant_id': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
    'bus_id': [1, 1, 5, 7, 7, 7, 8],
    'type': ['solar', 'coal', 'wind', 'solar', 'solar', 'ng', 'wind'],
    'Pmax': [15, 30, 10, 12, 8, 20, 15]
    }

mock_grid = MockGrid(
    grid_attrs={'branch': mock_branch, 'bus': mock_bus, 'plant': mock_plant})


class TestStubTopologyHelpers(unittest.TestCase):

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


class TestIdentifyMesh(unittest.TestCase):

    def setUp(self):
        # Build dummy congu and congl dataframes, containing barrier cruft
        num_hours = 100
        branch_indices = mock_branch['branch_id']
        num_branches = len(branch_indices)
        congu_data = np.ones((num_hours, num_branches)) * 1e-9
        congl_data = np.ones((num_hours, num_branches)) * 1e-10
        columns = mock_branch['branch_id']
        congu = pd.DataFrame(
            congu_data, index=range(num_hours), columns=columns)
        congl = pd.DataFrame(
            congl_data, index=range(num_hours), columns=columns)
        # Populate with dummy data
        # Branch 101 will have frequent, low congestion
        congu[101].iloc[-15:] = 1
        # Branch 102 will have less frequent, but greater congestion
        congu[102].iloc[:8] = 6
        # Branch 103 will have only occassional congestion, but very high
        congu[103].iloc[10:13] = 20
        congl[103].iloc[20:23] = 30
        # Build dummy change table
        ct = {'branch': {'branch_id': {b: 1 for b in branch_indices}}}

        # Finally, combine all of this into a MockScenario
        self.mock_scenario = MockScenario(
            grid_attrs={
                'branch': mock_branch,
                'bus': mock_bus,
                'plant': mock_plant,
                },
            congu=congu,
            congl=congl,
            ct=ct,
            )

    # These tests use the default 'branch' ranking: [103, 102, 101]
    def test_identify_mesh_branch_upgrades_default(self):
        # Not enough branches
        with self.assertRaises(ValueError):
            _identify_mesh_branch_upgrades(self.mock_scenario)

    def test_identify_mesh_branch_upgrades_n_4(self):
        # Not enough congest branches (barrier cruft values don't count)
        with self.assertRaises(ValueError):
            branches = _identify_mesh_branch_upgrades(
                self.mock_scenario, upgrade_n=4)

    def test_identify_mesh_branch_upgrades_n_3(self):
        expected_return = {101, 102, 103}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=3)
        self.assertEqual(branches, expected_return)

    def test_identify_mesh_branch_upgrades_n_2(self):
        expected_return = {102, 103}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=2)
        self.assertEqual(branches, expected_return)

    def test_identify_mesh_branch_upgrades_quantile90(self):
        # Fewer branches are congested for >= 10% of the time
        expected_return = {101}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=1, quantile=0.9)
        self.assertEqual(branches, expected_return)

    # These tests use the 'MW' ranking: [102, 101, 103]
    # This happens because 101 is very small, 102 is small (compared to 103)
    def test_identify_mesh_MW_n_3(self):
        expected_return = {101, 102, 103}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=3, method='MW')
        self.assertEqual(branches, expected_return)

    def test_identify_mesh_MW_n_2(self):
        expected_return = {101, 102}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=2, method='MW')
        self.assertEqual(branches, expected_return)

    def test_identify_mesh_MW_n_2_allow_list(self):
        expected_return = {102, 103}
        allow_list = {102, 103, 104}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=2, method='MW', allow_list=allow_list)
        self.assertEqual(branches, expected_return)

    def test_identify_mesh_MW_n_2_deny_list(self):
        expected_return = {101, 103}
        deny_list = [102, 105]
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=2, method='MW', deny_list=deny_list)
        self.assertEqual(branches, expected_return)

    def test_identify_mesh_MW_n_1(self):
        expected_return = {102}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=1, method='MW')
        self.assertEqual(branches, expected_return)

    # These tests use the 'MWmiles' ranking: [101, 102, 103]
    # This happens because 101 is zero-distance, 102 is short (compared to 103)
    def test_identify_mesh_MWmiles_n_3(self):
        expected_return = {101, 102, 103}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=3, method='MWmiles')
        self.assertEqual(branches, expected_return)

    def test_identify_mesh_MWmiles_n_2(self):
        expected_return = {101, 102}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=2, method='MWmiles')
        self.assertEqual(branches, expected_return)

    def test_identify_mesh_MWmiles_n_1(self):
        expected_return = {101}
        branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=1, method='MWmiles')
        self.assertEqual(branches, expected_return)

    # What about a made-up method?
    def test_identify_mesh_bad_method(self):
        with self.assertRaises(ValueError):
            branches = _identify_mesh_branch_upgrades(
            self.mock_scenario, upgrade_n=2, method='does not exist')


class TestConstructCompositeAllowlist(unittest.TestCase):

    def test_none_none(self):
        branch_list = mock_branch['branch_id'].copy()
        composite_allow_list = _construct_composite_allow_list(
            mock_branch['branch_id'].copy(), None, None)
        self.assertEqual(composite_allow_list, set(branch_list))

    def test_good_allow_list(self):
        allow_list = list(range(101, 105))
        composite_allow_list = _construct_composite_allow_list(
            mock_branch['branch_id'].copy(), allow_list, None)
        self.assertEqual(composite_allow_list, set(allow_list))

    def test_good_deny_list(self):
        deny_list = list(range(101, 105))
        composite_allow_list = _construct_composite_allow_list(
            mock_branch['branch_id'].copy(), None, deny_list)
        self.assertEqual(composite_allow_list, set(range(105, 109)))

    def test_allow_list_and_deny_list_failure(self):
        allow_list = list(range(101, 105))
        deny_list = list(range(105, 109))
        with self.assertRaises(ValueError):
            _construct_composite_allow_list(
                mock_branch['branch_id'].copy(), allow_list, deny_list)

    def test_bad_allow_list_value(self):
        allow_list = list(range(101, 110))
        with self.assertRaises(ValueError):
            _construct_composite_allow_list(
                mock_branch['branch_id'].copy(), allow_list, None)

    def test_bad_allow_list_entry_type(self):
        allow_list = [str(i) for i in range(101, 105)]
        with self.assertRaises(ValueError):
            _construct_composite_allow_list(
                mock_branch['branch_id'].copy(), allow_list, None)

    def test_bad_deny_list_value(self):
        deny_list = list(range(108, 110))
        with self.assertRaises(ValueError):
            _construct_composite_allow_list(
                mock_branch['branch_id'].copy(), None, deny_list)

    def test_bad_deny_list_type(self):
        with self.assertRaises(TypeError):
            _construct_composite_allow_list(
                mock_branch['branch_id'].copy(), None, '108')


class TestIncrementBranch(unittest.TestCase):

    def setUp(self):
        self.ct = {
            # These data aren't used, but we make sure they don't get changed.
            'demand': {'zone_id': {'W': 1.1, 'E': 1.2}},
            'solar': {'zone_id': {'W': 1.5, 'E': 1.7}},
            'wind': {'zone_id': {'E': 1.3, 'W': 2.1}},
            }
        self.ref_scenario = MockScenario(
            grid_attrs={
                'branch': mock_branch,
                'bus': mock_bus,
                'plant': mock_plant,
                },
            ct={
                'branch': {'branch_id': {101: 1.5, 102: 2.5, 103: 2, 105: 4}},
                # These shouldn't get used
                'coal': {'zone_id': {'E': 2, 'W': 0}},
                'demand': {'zone_id': {'W': 0.9, 'E': 0.8}},
                }
            )
        orig_ct = self.ref_scenario.state.get_ct()
        self.orig_branch_scaling = orig_ct['branch']['branch_id']

    def test_increment_branch_scaling_ref_only(self):
        change_table = MockChangeTable(grid=mock_grid, ct=self.ct)
        expected_ct = self.ct.copy()
        expected_ct['branch'] = {'branch_id': self.orig_branch_scaling.copy()}
        self.assertNotEqual(change_table.ct, expected_ct)
        _increment_branch_scaling(
            change_table, branch_ids=set(), ref_scenario=self.ref_scenario)
        self.assertEqual(change_table.ct, expected_ct)

    def test_increment_branch_scaling_ref_and_increment(self):
        change_table = MockChangeTable(grid=mock_grid, ct=self.ct)
        expected_ct = self.ct.copy()
        expected_ct['branch'] = {'branch_id': self.orig_branch_scaling.copy()}
        expected_ct['branch']['branch_id'][102] = 3.5
        expected_ct['branch']['branch_id'][103] = 3
        expected_ct['branch']['branch_id'][107] = 2
        self.assertNotEqual(change_table.ct, expected_ct)
        _increment_branch_scaling(
            change_table,
            branch_ids={102, 103, 107},
            ref_scenario=self.ref_scenario)
        self.assertEqual(change_table.ct, expected_ct)

    def test_increment_branch_scaling_ref_and_custom_increment(self):
        change_table = MockChangeTable(grid=mock_grid, ct=self.ct)
        expected_ct = self.ct.copy()
        expected_ct['branch'] = {'branch_id': self.orig_branch_scaling.copy()}
        expected_ct['branch']['branch_id'][101] = 2.0
        expected_ct['branch']['branch_id'][105] = 4.5
        expected_ct['branch']['branch_id'][106] = 1.5
        self.assertNotEqual(change_table.ct, expected_ct)
        _increment_branch_scaling(
            change_table,
            branch_ids={101, 105, 106},
            ref_scenario=self.ref_scenario,
            value=0.5)
        self.assertEqual(change_table.ct, expected_ct)

    def test_increment_branch_scaling_ref_and_ct_and_increment1(self):
        # Our change_table branch should get over-written by increment
        change_table = MockChangeTable(grid=mock_grid, ct=self.ct)
        change_table.ct['branch'] = {'branch_id': {101: 2}}
        expected_ct = change_table.ct.copy()
        expected_ct['branch'] = {'branch_id': self.orig_branch_scaling.copy()}
        expected_ct['branch']['branch_id'][101] = 2.5
        self.assertNotEqual(change_table.ct, expected_ct)
        _increment_branch_scaling(
            change_table, branch_ids={101}, ref_scenario=self.ref_scenario)
        self.assertEqual(change_table.ct, expected_ct)

    def test_increment_branch_scaling_ref_and_ct_and_increment2(self):
        # Our change_table branch should NOT get over-written by increment
        change_table = MockChangeTable(grid=mock_grid, ct=self.ct)
        change_table.ct['branch'] = {'branch_id': {101: 3}}
        expected_ct = change_table.ct.copy()
        expected_ct['branch'] = {'branch_id': self.orig_branch_scaling.copy()}
        expected_ct['branch']['branch_id'][101] = 3
        self.assertNotEqual(change_table.ct, expected_ct)
        _increment_branch_scaling(
            change_table, branch_ids={101}, ref_scenario=self.ref_scenario)
        self.assertEqual(change_table.ct, expected_ct)


class TestScaleRenewableStubs(unittest.TestCase):

    def test_empty_ct_inplace_default(self):
        expected_ct = {'branch': {'branch_id': {103: (11/8), 107: (21/15)}}}
        change_table = MockChangeTable(mock_grid)
        returned = scale_renewable_stubs(change_table, verbose=False)
        self.assertIsNone(returned)
        self.assertEqual(change_table.ct, expected_ct)

    def test_empty_ct_inplace_true(self):
        expected_ct = {'branch': {'branch_id': {103: (11/8), 107: (21/15)}}}
        change_table = MockChangeTable(mock_grid)
        returned = scale_renewable_stubs(change_table, verbose=False)
        self.assertIsNone(returned)
        self.assertEqual(change_table.ct, expected_ct)

    def test_empty_ct_inplace_false(self):
        expected_ct = {'branch': {'branch_id': {103: (11/8), 107: (21/15)}}}
        change_table = MockChangeTable(mock_grid)
        returned = scale_renewable_stubs(
            change_table, inplace=False, verbose=False)
        self.assertEqual(change_table.ct, {})
        self.assertEqual(returned, expected_ct)

    def test_empty_ct_no_fuzz(self):
        expected_ct = {'branch': {'branch_id': {103: (10/8), 107: (20/15)}}}
        change_table = MockChangeTable(mock_grid)
        returned = scale_renewable_stubs(change_table, fuzz=0, verbose=False)
        self.assertIsNone(returned)
        self.assertEqual(change_table.ct, expected_ct)

    def test_existing_ct_unrelated_branch_id(self):
        ct = {'branch': {'branch_id': {105: 2}}}
        change_table = MockChangeTable(mock_grid, ct=ct)
        expected_ct = {
            'branch': {'branch_id': {103: (11/8), 105:2, 107: (21/15)}}}
        scale_renewable_stubs(change_table, verbose=False)
        self.assertEqual(change_table.ct, expected_ct)

    def test_existing_ct_zone_id_wind(self):
        ct = {'wind': {'zone_id': {'E': 2}}}
        change_table = MockChangeTable(mock_grid, ct=ct)
        expected_ct = {
            'wind': {'zone_id': {'E': 2}},
            'branch': {'branch_id': {103: (21/8), 104: (31/25), 107: (21/15)}}
            }
        scale_renewable_stubs(change_table, verbose=False)
        self.assertEqual(change_table.ct, expected_ct)

    def test_existing_ct_zone_id_solar_wind(self):
        ct = {
            'wind': {'zone_id': {'E': 2}},
            'solar': {'zone_id': {'W': 3}},
            }
        change_table = MockChangeTable(mock_grid, ct=ct)
        expected_ct = {
            'wind': {'zone_id': {'E': 2}},
            'solar': {'zone_id': {'W': 3}},
            'branch': {'branch_id': {
                103: (21/8), 104: (31/25), 107: (61/15), 108: (61/25)}},
            }
        scale_renewable_stubs(change_table, verbose=False)
        self.assertEqual(change_table.ct, expected_ct)
