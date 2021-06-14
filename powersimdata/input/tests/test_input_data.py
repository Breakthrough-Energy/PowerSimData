import pytest

from powersimdata.input.input_data import InputHelper, _check_field


def test_get_file_components():
    s_info = {"id": "123"}
    ct_file, _ = InputHelper.get_file_components(s_info, "ct")
    grid_file, from_dir = InputHelper.get_file_components(s_info, "grid")
    assert "123_ct.pkl" == ct_file
    assert "123_grid.mat" == grid_file
    assert ("data", "input") == from_dir


def test_check_field():
    _check_field("demand")
    _check_field("hydro")
    with pytest.raises(ValueError):
        _check_field("foo")
        _check_field("coal")
