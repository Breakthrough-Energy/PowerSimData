import pytest

from powersimdata.scenario.scenario import Scenario
from powersimdata.input.scaler import ScaleProfile


@pytest.fixture(scope="module")
def scenario():
    return Scenario('519')


@pytest.fixture(scope="module")
def hydro_from_scenario(scenario):
    return scenario.state.get_hydro()


@pytest.fixture(scope="module")
def wind_from_scenario(scenario):
    return scenario.state.get_wind()


@pytest.fixture(scope="module")
def solar_from_scenario(scenario):
    return scenario.state.get_solar()


@pytest.fixture(scope="module")
def demand_from_scenario(scenario):
    return scenario.state.get_demand()


@pytest.fixture(scope="module")
def scaled_profile(scenario):
    return ScaleProfile(scenario.ssh,
                        scenario.info['id'],
                        scenario.state.grid,
                        scenario.state.ct)


@pytest.mark.integration
def test_demand_is_scaled(scenario, demand_from_scenario, scaled_profile):
    scaled_demand = scaled_profile.get_demand()

    assert demand_from_scenario.equals(scaled_demand)


@pytest.mark.integration
def test_solar_is_scaled(scenario, solar_from_scenario, scaled_profile):
    scaled_solar = scaled_profile.get_solar()

    assert solar_from_scenario.equals(scaled_solar)


@pytest.mark.integration
def test_wind_is_scaled(scenario, wind_from_scenario, scaled_profile):
    scaled_wind = scaled_profile.get_wind()

    assert wind_from_scenario.equals(scaled_wind)


@pytest.mark.integration
def test_hydro_is_scaled(scenario, hydro_from_scenario, scaled_profile):
    scaled_hydro = scaled_profile.get_hydro()

    assert hydro_from_scenario.equals(scaled_hydro)
