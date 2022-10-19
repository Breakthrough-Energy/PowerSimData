import pytest

from powersimdata.input.input_data import InputData

_input_data = InputData()


def test_get_file_components():
    s_info = {"id": "123"}
    ct_file = _input_data._get_file_path(s_info, "ct")
    grid_file = _input_data._get_file_path(s_info, "grid")
    assert "data/input/123_ct.pkl" == ct_file
    assert "data/input/123_grid.pkl" == grid_file


def test_check_field():
    _check_field = _input_data._check_field
    _check_field("grid")
    _check_field("ct")
    with pytest.raises(ValueError):
        _check_field("foo")
        _check_field("solar")
