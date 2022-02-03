import pytest

from powersimdata.data_access.context import Context
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

    s.print_scenario_info()
    s.create_scenario()

    # hack to use truncated profiles so the test runs quickly
    s.info["grid_model"] = "test_usa_tamu"
    s.prepare_simulation_input()
