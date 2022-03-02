from fs.tempfs import TempFS

from powersimdata.data_access.profile_helper import ProfileHelper, get_profile_version


def test_get_profile_version():
    with TempFS() as tmp_fs:
        grid_model = "usa_tamu"
        sub_fs = tmp_fs.makedirs(f"raw/{grid_model}", recreate=True)
        sub_fs.touch("solar_vOct2022.csv")
        sub_fs.touch("foo_v1.0.1.csv")
        v_solar = get_profile_version(tmp_fs, grid_model, "solar")
        v_foo = get_profile_version(tmp_fs, grid_model, "foo")
        v_missing = get_profile_version(tmp_fs, grid_model, "missing")
        assert "vOct2022" == v_solar[0]
        assert "v1.0.1" == v_foo[0]
        assert [] == v_missing


def test_get_file_components():
    s_info = {"base_wind": "v8", "grid_model": "europe"}
    file_name, from_dir = ProfileHelper.get_file_components(s_info, "wind")
    assert "wind_v8.csv" == file_name
    assert ("raw", "europe") == from_dir
