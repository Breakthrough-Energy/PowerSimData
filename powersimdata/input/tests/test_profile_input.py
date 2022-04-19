from fs.tempfs import TempFS

from powersimdata.data_access.data_access import get_profile_version
from powersimdata.input.profile_input import ProfileInput


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


def test_get_file_path():
    s_info = {"base_wind": "v8", "grid_model": "europe"}
    path = ProfileInput()._get_file_path(s_info, "wind")
    assert "raw/europe/wind_v8.csv" == path
