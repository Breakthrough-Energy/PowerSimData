from powersimdata.data_access.profile_helper import ProfileHelper


def test_parse_version_default():
    assert [] == ProfileHelper.parse_version("usa_tamu", "solar", {})


def test_parse_version_missing_key():
    version = {"solar": ["v123"]}
    assert [] == ProfileHelper.parse_version("usa_tamu", "solar", version)


def test_parse_version():
    expected = ["v123", "v456"]
    version = {"usa_tamu": {"solar": expected}}
    assert expected == ProfileHelper.parse_version("usa_tamu", "solar", version)
    assert [] == ProfileHelper.parse_version("usa_tamu", "hydro", version)


def test_get_file_components():
    s_info = {"base_wind": "v8", "grid_model": "europe"}
    file_name, from_dir = ProfileHelper.get_file_components(s_info, "wind")
    assert "wind_v8.csv" == file_name
    assert ("raw", "europe") == from_dir
