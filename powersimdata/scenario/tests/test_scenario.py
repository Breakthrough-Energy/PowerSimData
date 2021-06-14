import pytest

from powersimdata.scenario.scenario import Scenario


@pytest.mark.integration
@pytest.mark.ssh
def test_bad_scenario_name():
    # This test will fail if we do add a scenario with this name
    with pytest.raises(ValueError):
        Scenario("this_scenario_does_not_exist")
