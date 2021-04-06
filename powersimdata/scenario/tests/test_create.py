import pytest

from powersimdata.scenario.scenario import Scenario


@pytest.mark.integration
@pytest.mark.ssh
def test_get_bus_demand():
    scenario = Scenario("")
    scenario.state.set_grid(interconnect="Texas")
    scenario.state.builder.set_base_profile("demand", "vJan2021")
    scenario.state.get_bus_demand()
