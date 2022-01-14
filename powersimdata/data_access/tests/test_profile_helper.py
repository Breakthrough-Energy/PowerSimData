from fs.tempfs import TempFS

from powersimdata.data_access.profile_helper import ProfileHelper, _get_profile_version


def test_get_profile_version():
    with TempFS() as tmp_fs:
        tfs = tmp_fs.makedirs("raw/usa_tamu", recreate=True)
        tfs.touch("solar_vOct2022.csv")
        tfs.touch("foo_v1.0.1.csv")
        v_solar = _get_profile_version(tfs, "solar")
        v_foo = _get_profile_version(tfs, "foo")
        v_missing = _get_profile_version(tfs, "missing")
        assert "vOct2022" == v_solar[0]
        assert "v1.0.1" == v_foo[0]
        assert [] == v_missing


def test_get_file_components():
    s_info = {"base_wind": "v8", "grid_model": "europe"}
    file_name, from_dir = ProfileHelper.get_file_components(s_info, "wind")
    assert "wind_v8.csv" == file_name
    assert ("raw", "europe") == from_dir
