from powersimdata.scenario.analyze import Analyze
from powersimdata.scenario.scenario import Scenario


def _check_scenario_is_in_analyze_state(scenario):
    """Ensure that scenario is a Scenario object in the analyze state.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :raises TypeError: if scenario is not a Scenario instance.
    :raises ValueError: if Scenario object is not in analyze state.
    """
    if not isinstance(scenario, Scenario):
        raise TypeError(f"scenario must be a {Scenario} object")
    if not isinstance(scenario.state, Analyze):
        raise ValueError("scenario must in analyze state")
