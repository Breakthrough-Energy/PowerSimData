import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from powersimdata.design.generation.clean_capacity_scaling import (
    add_new_capacities_collaborative,
    add_new_capacities_independent,
    add_shortfall_to_targets,
)


def test_independent_new_capacity():
    area_names = ["Pacific", "Atlantic", "Arctic", "Indian"]
    # Atlantic tests a 'simple' case
    # Pacific tests expected additional curtailment
    # Arctic tests external additional clean energy
    # Indian tests new capacity solar percentage
    targets = pd.DataFrame(
        {
            "ce_target_fraction": [0.25, 0.3, 0.25, 0.25],
            "allowed_resources": [
                "solar,wind,geo",
                "solar, wind, geo, hydro",
                "solar,wind,geo",
                "solar, wind, geo",
            ],
            "demand": [2e8, 3e8, 2e8, 2e8],
            "solar_percentage": [None, None, None, 0.75],
            "external_ce_addl_historical_amount": [0, 0, 1.4e7, 0],
            "geo.prev_capacity": [4000, 4500, 4000, 4000],
            "geo.prev_cap_factor": [1, 1, 1, 1],
            "geo.prev_generation": [8e6, 8.5e6, 8e6, 8e6],
            "hydro.prev_capacity": [3900, 4400, 3900, 3900],
            "hydro.prev_cap_factor": [1, 1, 1, 1],
            "hydro.prev_generation": [7e6, 7.5e6, 7e6, 7e6],
            "solar.prev_capacity": [3700, 4200, 3700, 3700],
            "solar.prev_cap_factor": [0.25, 0.3, 0.215379, 0.215379],
            "solar.prev_generation": [8.1252e6, 1.106784e7, 7e6, 7e6],
            "wind.prev_capacity": [3600, 4100, 3600, 3600],
            "wind.prev_cap_factor": [0.4, 0.35, 0.347854, 0.347854],
            "wind.prev_generation": [1.264896e7, 1.260504e7, 1.1e7, 1.1e7],
        },
        index=area_names,
    )
    addl_curtailment = pd.DataFrame(
        {
            "geo": [0, 0, 0, 0],
            "hydro": [0, 0, 0, 0],
            "solar": [0.4, 0, 0, 0],
            "wind": [0, 0, 0, 0],
        },
        index=area_names,
    )
    expected_return = pd.DataFrame(
        {
            "solar.next_capacity": [
                (3700 + 4481.582),
                (4200 + 8928.948),
                (3700 + 2055.556),
                (3700 + 8246.260),
            ],
            "wind.next_capacity": [
                (3600 + 4360.459),
                (4100 + 8716.354),
                (3600 + 2000),
                (3600 + 2748.753),
            ],
            "prev_ce_generation": [2.877416e7, 3.967288e7, 2.6e7, 2.6e7],
            "ce_shortfall": [2.122584e7, 5.032712e7, 1e7, 2.4e7],
        },
        index=area_names,
    )
    targets = add_shortfall_to_targets(targets)
    targets = add_new_capacities_independent(
        targets, scenario_length=8784, addl_curtailment=addl_curtailment
    )
    test_columns = [
        "prev_ce_generation",
        "ce_shortfall",
        "solar.next_capacity",
        "wind.next_capacity",
    ]
    assert_frame_equal(targets[test_columns], expected_return[test_columns])


@pytest.fixture
def collaborative_test_targets():
    targets = pd.DataFrame(
        {
            "ce_target_fraction": [0.25, 0.4, 0],
            "allowed_resources": [
                "solar, wind, geo",
                "solar, wind, geo, hydro, nuclear",
                "polarbears",
            ],
            "demand": [2e8, 3e8, 1e8],
            "external_ce_addl_historical_amount": [0, 0, 0],
            "geo.prev_capacity": [4000, 4500, 0],
            "geo.prev_cap_factor": [1, 1, 0],
            "geo.prev_generation": [8e6, 8.5e6, 0],
            "hydro.prev_capacity": [3900, 4400, 0],
            "hydro.prev_cap_factor": [1, 1, 0],
            "hydro.prev_generation": [7e6, 7.5e6, 0],
            "nuclear.prev_capacity": [4300, 4300, 0],
            "nuclear.prev_cap_factor": [1, 1, 0],
            "nuclear.prev_generation": [6.5e6, 6.5e6, 0],
            "solar.prev_capacity": [3700, 4200, 5000],
            "solar.prev_cap_factor": [0.215379, 0.284608, 0.45],
            "solar.prev_generation": [7e6, 1.05e7, (5000 * 0.45 * 8784)],
            "wind.prev_capacity": [3600, 4100, 4000],
            "wind.prev_cap_factor": [0.347855, 0.319317, 0.5],
            "wind.prev_generation": [1.1e7, 1.15e7, (4000 * 0.5 * 8784)],
        },
        index=["Pacific", "Atlantic", "Arctic"],
    )
    return targets


def test_collaborative_two_areas_overgeneration(collaborative_test_targets):
    targets = collaborative_test_targets.copy()
    targets.loc["Pacific", "ce_target_fraction"] = 1e-9
    targets.drop("Arctic", inplace=True)
    targets = add_shortfall_to_targets(targets)
    targets = add_new_capacities_collaborative(targets, scenario_length=8784)
    expected_return = pd.DataFrame(
        {
            "solar.next_capacity": [(3700 + 4578.75), (4200 + 5197.5)],
            "wind.next_capacity": [(3600 + 4455), (4100 + 5073.75)],
        },
        index=["Pacific", "Atlantic"],
    )
    assert_frame_equal(
        targets[["solar.next_capacity", "wind.next_capacity"]],
        expected_return[["solar.next_capacity", "wind.next_capacity"]],
    )


def test_collaborative_two_areas_addl_curtailment(collaborative_test_targets):
    targets = collaborative_test_targets.copy()
    targets.drop("Arctic", inplace=True)
    targets = add_shortfall_to_targets(targets)
    targets = add_new_capacities_collaborative(
        targets, scenario_length=8784, addl_curtailment={"solar": 0.07, "wind": 0.13}
    )
    expected_return = pd.DataFrame(
        {
            "solar.next_capacity": [(3700 + 10269.18), (4200 + 11656.9)],
            "wind.next_capacity": [(3600 + 9991.63), (4100 + 11379.36)],
        },
        index=["Pacific", "Atlantic"],
    )
    assert_frame_equal(
        targets[["solar.next_capacity", "wind.next_capacity"]],
        expected_return[["solar.next_capacity", "wind.next_capacity"]],
    )


def test_collaborative_three_areas_one_nonparticipating(collaborative_test_targets):
    targets = collaborative_test_targets.copy()
    targets = add_shortfall_to_targets(targets)
    targets = add_new_capacities_collaborative(targets, scenario_length=8784)
    expected_return = pd.DataFrame(
        {
            "solar.next_capacity": [(3700 + 9203.75), (4200 + 10447.5), 5000],
            "wind.next_capacity": [(3600 + 8955), (4100 + 10198.75), 4000],
        },
        index=["Pacific", "Atlantic", "Arctic"],
    )
    assert_frame_equal(
        targets[["solar.next_capacity", "wind.next_capacity"]],
        expected_return[["solar.next_capacity", "wind.next_capacity"]],
    )


def test_collaborative_two_areas_addl_external(collaborative_test_targets):
    targets = collaborative_test_targets.copy()
    targets.drop("Arctic", inplace=True)
    targets.loc["Pacific", "external_ce_addl_historical_amount"] = 4e6
    targets = add_shortfall_to_targets(targets)
    targets = add_new_capacities_collaborative(targets, scenario_length=8784)
    expected_return = pd.DataFrame(
        {
            "solar.next_capacity": [(3700 + 8833.75), (4200 + 10027.5)],
            "wind.next_capacity": [(3600 + 8595), (4100 + 9788.75)],
        },
        index=["Pacific", "Atlantic"],
    )
    assert_frame_equal(
        targets[["solar.next_capacity", "wind.next_capacity"]],
        expected_return[["solar.next_capacity", "wind.next_capacity"]],
    )
