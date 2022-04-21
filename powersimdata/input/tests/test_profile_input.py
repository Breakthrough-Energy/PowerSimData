from fs.tempfs import TempFS

from powersimdata.input.electrified_demand_input import (
    get_profile_version as get_profile_version_elec,
)
from powersimdata.input.profile_input import ProfileInput, get_profile_version


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


def test_get_profile_version_electrification():
    with TempFS() as tmp_fs:
        grid_model = "usa_tamu"
        kind = "building"
        end_use = "res_cooking"
        tech = "standard_heat_pump"
        sub_fs = tmp_fs.makedirs(f"raw/{grid_model}/{kind}", recreate=True)
        sub_fs.touch(f"{end_use}_{tech}_v1.csv")
        version = get_profile_version_elec(tmp_fs, grid_model, kind, end_use, tech)
        v_missing = get_profile_version_elec(
            tmp_fs, grid_model, kind, end_use, "fake_tech"
        )
        assert "v1" == version[0]
        assert [] == v_missing
