import unittest

import pandas as pd
from numpy.testing import assert_array_equal, assert_array_almost_equal
from pandas.testing import assert_frame_equal, assert_series_equal

from powersimdata.design.investment.investment_costs import (
    _calculate_ac_inv_costs,
    _calculate_dc_inv_costs,
    _calculate_gen_inv_costs

)
from powersimdata.tests.mock_scenario import MockScenario
from powersimdata.tests.mock_grid import MockGrid

# branch 10-12 from Seattle (s3, p1, NWPP Coal) to San Francisco (s25, p9, NP15) (~679 miles)
# branch 13-14 are transformers (0 miles)
mock_branch = {
    "branch_id": [10, 11, 12, 13, 14],
    "rateA": [0, 10, 1100, 30, 40],
    "from_lat": [47.61, 47.61, 47.61, 47.61, 47.61],
    "from_lon": [-122.33, -122.33, -122.33, -122.33, -122.33],
    "to_lat": [37.78, 37.78, 37.78, 47.61, 47.61],
    "to_lon": [-122.42, -122.42, -122.42, -122.33, -122.33],
    "from_bus_id": [1, 1, 3, 3, 4],
    "to_bus_id": [2, 2, 2, 3, 4],
    "branch_device_type": 3 * ["Line"] + 2 * ["Transformer"],
}

# bus_id is the index
mock_bus = {
    "bus_id": [1, 2, 3, 4],
    "lat": [47.61, 37.78, 47.61, 47.61],
    "lon": [-122.33, -122.42, -122.42, -122.42],
    "baseKV": [100, 346, 230, 800],
}

mock_plant = {
    "plant_id": ["A", "B", "C", "D", "E", "F", "G"],
    "bus_id": [1, 1, 2, 3, 3, 3, 4],
    "type": ["solar", "coal", "wind", "solar", "solar", "ng", "wind"],
    "Pmax": [15, 30, 10, 12, 8, 20, 15],
}

mock_dcline = {
    "dcline_id": [5],
    'Pmax': [10],
    "from_bus_id": [1],
    "to_bus_id": [2],
}

grid_attrs = {"plant": mock_plant, "bus": mock_bus, "branch": mock_branch, "dcline": mock_dcline}



class TestCalculateACInvCosts(unittest.TestCase):
    def setUp(self):
        self.grid = MockGrid(grid_attrs)
        self.expected_keys = {"line_cost", "transformer_cost"}

    def _check_expected_values(self, ac_cost, expected_ac_cost):
        """Check for proper structure and that values match expected.

        :param dict ac_cost: dict of investment cost.
        :param dict expected_ac_cost: dict of expected investment cost.
        """

        self.assertIsInstance(ac_cost, dict, "dict not returned")
        self.assertEqual(
            self.expected_keys, ac_cost.keys(), msg="Dict keys not as expected"
        )
        for v in ac_cost.values():
            self.assertIsInstance(v, (float, int))
        for k in expected_ac_cost.keys():
            err_msg = "Did not get expected value for " + str(k)
            self.assertAlmostEqual(ac_cost[k], expected_ac_cost[k], places=2, msg=err_msg)

    def test_calculate_ac_inv_costs(self):
        expected_ac_cost = {
                            "line_cost": (679.2035515226485 * (1 + 2.25)/2.0) * (0 + 3666.67 * 10 + 1500 * 1100), # (miles * (reg_mult1 + reg_cost2)/2 ) * (basecost * rateA)
                            "transformer_cost": 5500000 + 42500000, #(HVDCTerminalcost + HVDCcost)
                            }
        ac_cost = _calculate_ac_inv_costs(self.grid, "2025")
        self._check_expected_values(ac_cost, expected_ac_cost)

class TestCalculateDCInvCosts(unittest.TestCase):
    def setUp(self):
        self.grid = MockGrid(grid_attrs)
        #self.expected_keys = {"line_cost", "transformer_cost"}

    def test_calculate_dc_inv_costs(self):
        expected_dc_cost = 10 * 679.2035515226485 * 457.1428571 + 550000000
        dc_cost = _calculate_dc_inv_costs(self.grid, "2025")
        self.assertAlmostEqual(dc_cost, expected_dc_cost, places=2, msg="Did not get expected value for dc_cost.")