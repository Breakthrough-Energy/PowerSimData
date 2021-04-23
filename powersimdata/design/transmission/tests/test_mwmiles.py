import unittest

from powersimdata.design.transmission.mwmiles import _calculate_mw_miles
from powersimdata.tests.mock_grid import MockGrid

# branch 11 from Seattle to San Francisco (~679 miles)
# branch 12 from Seattle to Spokane (~229 miles)
# branch 13-15 are transformers (0 miles)
mock_branch = {
    "branch_id": [11, 12, 13, 14, 15],
    "rateA": [10, 20, 30, 40, 50],
    "from_lat": [47.61, 47.61, 47.61, 47.61, 47.61],
    "from_lon": [-122.33, -122.33, -122.33, -122.33, -122.33],
    "to_lat": [37.78, 47.66, 47.61, 47.61, 47.61],
    "to_lon": [-122.42, -117.43, -122.33, -122.33, -122.33],
    "branch_device_type": 2 * ["Line"] + 3 * ["Transformer"],
    "x": 5 * [1],
}

expected_keys = {"mw_miles", "transformer_mw", "num_lines", "num_transformers"}


class TestCalculateMWMiles(unittest.TestCase):
    def setUp(self):
        self.grid = MockGrid(grid_attrs={"branch": mock_branch})

    def _check_expected_values(self, mw_miles, expected_mw_miles):
        """Check for proper structure and that values match expected.

        :param dict mw_miles: dict of upgrade metrics.
        :param dict expected_mw_miles: dict of expected upgrade metrics.
        """
        self.assertIsInstance(mw_miles, dict, "dict not returned")
        self.assertEqual(
            expected_keys, mw_miles.keys(), msg="Dict keys not as expected"
        )
        for v in mw_miles.values():
            self.assertIsInstance(v, (float, int))
        for k in expected_mw_miles.keys():
            err_msg = "Did not get expected value for " + str(k)
            self.assertAlmostEqual(mw_miles[k], expected_mw_miles[k], msg=err_msg)

    def test_calculate_mw_miles_no_scale(self):
        mock_ct = {"branch": {"branch_id": {}}}
        expected_mw_miles = {k: 0 for k in expected_keys}
        mw_miles = _calculate_mw_miles(self.grid, mock_ct)
        self._check_expected_values(mw_miles, expected_mw_miles)

    def test_calculate_mw_miles_one_line_scaled(self):
        mock_ct = {"branch": {"branch_id": {11: 2}}}
        expected_mw_miles = {
            "mw_miles": 6792.03551523,
            "transformer_mw": 0,
            "num_lines": 1,
            "num_transformers": 0,
        }
        mw_miles = _calculate_mw_miles(self.grid, mock_ct)
        self._check_expected_values(mw_miles, expected_mw_miles)

    def test_calculate_mw_miles_one_transformer_scaled(self):
        mock_ct = {"branch": {"branch_id": {13: 2.5}}}
        expected_mw_miles = {
            "mw_miles": 0,
            "transformer_mw": 45,
            "num_lines": 0,
            "num_transformers": 1,
        }
        mw_miles = _calculate_mw_miles(self.grid, mock_ct)
        self._check_expected_values(mw_miles, expected_mw_miles)

    def test_calculate_mw_miles_many_scaled(self):
        mock_ct = {"branch": {"branch_id": {11: 2, 12: 3, 13: 1.5, 14: 1.2, 15: 3}}}
        expected_mw_miles = {
            "mw_miles": 15917.06341095,
            "transformer_mw": 123,
            "num_lines": 2,
            "num_transformers": 3,
        }
        mw_miles = _calculate_mw_miles(self.grid, mock_ct)
        self._check_expected_values(mw_miles, expected_mw_miles)

    def test_calculate_mw_miles_many_scaled_one_branch_excluded(self):
        mock_ct = {"branch": {"branch_id": {11: 2, 12: 3, 13: 1.5, 14: 1.2, 15: 3}}}
        expected_mw_miles = {
            "mw_miles": 9125.027895725,
            "transformer_mw": 123,
            "num_lines": 1,
            "num_transformers": 3,
        }
        mw_miles = _calculate_mw_miles(self.grid, mock_ct, exclude_branches={11})
        self._check_expected_values(mw_miles, expected_mw_miles)

    def test_calculate_mw_miles_many_scaled_two_branches_excluded(self):
        mock_ct = {"branch": {"branch_id": {11: 2, 12: 3, 13: 1.5, 14: 1.2, 15: 3}}}
        expected_mw_miles = {
            "mw_miles": 9125.027895725,
            "transformer_mw": 108,
            "num_lines": 1,
            "num_transformers": 2,
        }
        mw_miles = _calculate_mw_miles(self.grid, mock_ct, exclude_branches=[11, 13])
        self._check_expected_values(mw_miles, expected_mw_miles)


if __name__ == "__main__":
    unittest.main()
