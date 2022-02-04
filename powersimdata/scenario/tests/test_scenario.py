import pytest

from powersimdata.data_access.context import Context
from powersimdata.scenario.delete import Delete
from powersimdata.scenario.scenario import Scenario
from powersimdata.tests.mock_context import MockContext


@pytest.mark.integration
@pytest.mark.ssh
def test_bad_scenario_name():
    # This test will fail if we do add a scenario with this name
    with pytest.raises(ValueError):
        Scenario("this_scenario_does_not_exist")


def test_scenario_workflow(monkeypatch):
    mock_context = MockContext()
    monkeypatch.setattr(Context, "get_data_access", mock_context.get_data_access)

    s = Scenario()
    print(s.state.name)

    s.set_grid(interconnect="Texas")

    s.set_name("test", "dummy")
    s.set_time("2016-01-01 00:00:00", "2016-01-01 03:00:00", "1H")

    s.set_base_profile("demand", "vJan2021")
    s.set_base_profile("hydro", "vJan2021")
    s.set_base_profile("solar", "vJan2021")
    s.set_base_profile("wind", "vJan2021")
    s.change_table.ct = {
        "wind": {
            "zone_id": {
                301: 1.1293320940114195,
                302: 2.2996731828360466,
                303: 1.1460693669609412,
                304: 1.5378918905751389,
                305: 1.6606575751914816,
            },
            "plant_id": {12912: 0},
        }
    }

    s.get_grid()
    s.get_ct()

    rfs = s.data_access.fs
    lfs = s.data_access.local_fs
    tmp_dir = s.data_access.tmp_folder(1)

    s.print_scenario_info()
    s.create_scenario()

    scenario_list = s.get_scenario_table()
    assert 1 == scenario_list.shape[0]

    for fs in (lfs, rfs):
        assert fs.exists("data/input/1_ct.pkl")

    # hack to use truncated profiles so the test runs quickly
    s.info["grid_model"] = "test_usa_tamu"
    s.prepare_simulation_input()

    tmp_files = rfs.listdir(tmp_dir)
    assert len(tmp_files) > 0

    s.change(Delete)
    s.delete_scenario(confirm=False)

    for fs in (rfs, lfs):
        assert not fs.exists(tmp_dir)
        assert len(fs.listdir("data/input")) == 0

    scenario_list = Scenario().get_scenario_table()
    assert 0 == scenario_list.shape[0]
