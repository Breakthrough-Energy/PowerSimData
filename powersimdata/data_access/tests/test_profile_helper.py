from powersimdata.data_access.profile_helper import ProfileHelper


def test_get_file_components():
    s_info = {"base_wind": "v8", "grid_model": "europe"}
    file_name, from_dir = ProfileHelper.get_file_components(s_info, "wind")
    assert "wind_v8.csv" == file_name
    assert ("raw", "europe") == from_dir
