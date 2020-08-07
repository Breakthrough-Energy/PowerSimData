import pytest

import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

from powersimdata.tests.mock_scenario import MockScenario
from powersimdata.design.clean_capacity_scaling import (
    add_resource_data_to_targets,
    add_demand_to_targets,
    add_shortfall_to_targets,
    add_new_capacities_independent,
    add_new_capacities_collaborative,
    create_change_table,
    calculate_clean_capacity_scaling,
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
            "wind": [0, 0, 0, 0,],
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
