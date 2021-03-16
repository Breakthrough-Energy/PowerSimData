import unittest

from powersimdata.design.transmission.statelines import _classify_interstate_intrastate
from powersimdata.tests.mock_grid import MockGrid

# branch_id is the index
mock_branch = {
    "branch_id": [1, 2, 3, 4, 5, 6, 7, 8],
    "from_zone_id": [10, 10, 10, 52, 216, 216, 216, 7],
    "to_zone_id": [10, 11, 12, 215, 301, 216, 301, 204],
}

expected_keys = {"interstate", "intrastate"}


class TestClassifyInterstateIntrastate(unittest.TestCase):
    def setUp(self):
        def check_expected(upgrades, expected_interstate, expected_intrastate):
            err_msg = "classify_interstate_intrastate should return a dict"
            self.assertIsInstance(upgrades, dict, err_msg)
            err_msg = "dict keys should be 'interstate' and 'intrastate'"
            self.assertEqual(upgrades.keys(), expected_keys, err_msg)
            for v in upgrades.values():
                self.assertIsInstance(v, list, "dict values should be lists")
                for b in v:
                    self.assertIsInstance(b, int, "branch_ids should be ints")
            err_msg = "interstate values not as expected"
            self.assertEqual(set(upgrades["interstate"]), expected_interstate, err_msg)
            err_msg = "intrastate values not as expected"
            self.assertEqual(set(upgrades["intrastate"]), expected_intrastate, err_msg)

        self.check_expected = check_expected
        self.mock_grid = MockGrid(grid_attrs={"branch": mock_branch})

    def test_classify_interstate_intrastate_empty_ct(self):
        mock_ct = {}
        expected_interstate = set()
        expected_intrastate = set()

        upgrades = _classify_interstate_intrastate(mock_ct, self.mock_grid)
        self.check_expected(upgrades, expected_interstate, expected_intrastate)

    def test_classify_interstate_intrastate_bad_ct(self):
        mock_ct = {"branch": {"branch_id": {9: 1.5}}}

        with self.assertRaises(ValueError):
            _classify_interstate_intrastate(mock_ct, self.mock_grid)

    def test_classify_interstate_intrastate_none(self):
        mock_ct = {"branch": {"branch_id": {}}}
        expected_interstate = set()
        expected_intrastate = set()

        upgrades = _classify_interstate_intrastate(mock_ct, self.mock_grid)
        self.check_expected(upgrades, expected_interstate, expected_intrastate)

    def test_classify_interstate_intrastate_two(self):
        mock_ct = {"branch": {"branch_id": {1: 2, 8: 10}}}
        expected_interstate = {8}
        expected_intrastate = {1}

        upgrades = _classify_interstate_intrastate(mock_ct, self.mock_grid)
        self.check_expected(upgrades, expected_interstate, expected_intrastate)

    def test_classify_interstate_intrastate_several(self):
        mock_ct = {
            "branch": {
                "branch_id": {
                    1: 2,
                    2: 3,
                    3: 1.5,
                    4: 4,
                    5: 1.1,
                    8: 10,
                }
            }
        }
        expected_interstate = {3, 8}
        expected_intrastate = {1, 2, 4, 5}

        upgrades = _classify_interstate_intrastate(mock_ct, self.mock_grid)
        self.check_expected(upgrades, expected_interstate, expected_intrastate)


if __name__ == "__main__":
    unittest.main()
