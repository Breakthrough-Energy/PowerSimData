import pytest

from powersimdata.scenario.check import _check_scenario_is_in_analyze_state
from powersimdata.tests.mock_scenario import MockScenario


@pytest.fixture
def mock_scenario():
    return MockScenario()


def test_check_scenario_is_in_analyze_state_argument_type():
    arg = (1, "foo")
    for a in arg:
        with pytest.raises(TypeError):
            _check_scenario_is_in_analyze_state(a)


def test_check_scenario_is_in_analyze_state_argument_value():
    input = MockScenario()
    input.state = "Create"
    with pytest.raises(ValueError):
        _check_scenario_is_in_analyze_state(input)


def test_check_scenario_is_in_analyze(mock_scenario):
    _check_scenario_is_in_analyze_state(mock_scenario)
