import pytest
from pandas.testing import assert_series_equal

from powersimdata.scenario.scenario import Scenario


@pytest.mark.integration
def test_get_demand_and_get_bus_demand():
    scenario = Scenario("")
    scenario.set_grid(interconnect="Texas")
    # Before we set the profile version, we should get errors trying to access
    with pytest.raises(Exception):
        scenario.get_bus_demand()
    with pytest.raises(Exception):
        scenario.get_demand()
    # After we set the profile version, we should get the right len (default full year)
    scenario.set_base_profile("demand", "vJan2021")
    assert len(scenario.get_bus_demand()) == 8784
    scenario.set_time("2016-01-01 00:00", "2016-01-03 23:00", "24H")
    demand = scenario.get_demand()
    bus_demand = scenario.get_bus_demand()
    assert len(demand) == 72
    assert len(bus_demand) == 72
    assert_series_equal(demand.sum(axis=1), bus_demand.sum(axis=1))
    unscaled_total_demand = demand.sum().sum()
    scenario.change_table.scale_demand(zone_id={301: 1.5})
    new_demand = scenario.get_demand()
    new_bus_demand = scenario.get_bus_demand()
    assert_series_equal(new_demand.sum(axis=1), new_bus_demand.sum(axis=1))
    assert new_demand.sum().sum() > unscaled_total_demand


@pytest.mark.integration
def test_get_solar():
    scenario = Scenario("")
    scenario.set_grid(interconnect="Texas")
    with pytest.raises(Exception):
        scenario.get_solar()
    scenario.set_base_profile("solar", "vJan2021")
    assert len(scenario.get_solar()) == 8784
    scenario.set_time("2016-01-01 00:00", "2016-01-03 23:00", "24H")
    assert len(scenario.get_solar()) == 72
