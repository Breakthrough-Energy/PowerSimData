import pandas as pd
import pytest

from powersimdata.design.generation.curtailment import temporal_curtailment
from powersimdata.tests.mock_scenario import MockScenario

mock_plant = {
    "plant_id": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "type": ["coal", "wind", "solar", "hydro", "ng", "nuclear"] * 2,
    "Pmax": [50, 50, 50, 50, 20, 60, 100, 50, 50, 50, 40, 120],
    "Pmin": [20, 0, 0, 0, 0, 30, 30, 0, 0, 0, 10, 75],
}

mock_demand = pd.DataFrame(
    {1: [350, 350, 325, 400, 500]},
)

mock_hydro = pd.DataFrame(
    {
        3: [25, 40, 50, 30, 0],
        9: [25, 40, 50, 30, 0],
    }
)

mock_solar = pd.DataFrame(
    {
        2: [20, 20, 20, 20, 20],
        8: [10, 20, 30, 40, 50],
    }
)

mock_wind = pd.DataFrame(
    {
        1: [0, 50, 0, 50, 0],
        7: [20, 30, 20, 30, 20],
    }
)


@pytest.fixture
def mock_scenario():
    return MockScenario(
        grid_attrs={"plant": mock_plant},
        demand=mock_demand,
        hydro=mock_hydro,
        solar=mock_solar,
        wind=mock_wind,
    )


def test_temporal_curtailment(mock_scenario):
    assert temporal_curtailment(mock_scenario) == pytest.approx(0.3361702)

    # Testing that "None" overrides the default simulation Pmin with the data Pmin
    curtailment = temporal_curtailment(mock_scenario, pmin_by_type={"ng": None})
    assert curtailment == pytest.approx(0.4)
    curtailment = temporal_curtailment(mock_scenario, pmin_by_id={10: None})
    assert curtailment == pytest.approx(0.4)

    # Testing that we can change replace the Pmin with relative-to-Pmax values
    curtailment = temporal_curtailment(mock_scenario, pmin_by_id={5: 1})
    assert curtailment == pytest.approx(0.35531915)
    curtailment = temporal_curtailment(mock_scenario, pmin_by_id={11: 1})
    assert curtailment == pytest.approx(0.37446809)
    curtailment = temporal_curtailment(mock_scenario, pmin_by_id={5: 1, 11: 1})
    assert curtailment == pytest.approx(0.39361702)
    curtailment = temporal_curtailment(mock_scenario, pmin_by_type={"nuclear": 1})
    assert curtailment == pytest.approx(0.39361702)
    curtailment = temporal_curtailment(mock_scenario, pmin_by_id={5: 1, 11: 0.99})
    assert curtailment == pytest.approx(0.38595744)
    curtailment = temporal_curtailment(mock_scenario, pmin_by_type={"nuclear": 0.98})
    assert curtailment == pytest.approx(0.37063830)
    # Testing that we can override by-type with by-id
    curtailment = temporal_curtailment(
        mock_scenario, pmin_by_type={"nuclear": 1}, pmin_by_id={11: 0.99}
    )
    assert curtailment == pytest.approx(0.38595744)

    # Testing that we can relax the Pmin of a profile resource by type
    assert temporal_curtailment(mock_scenario, pmin_by_type={"hydro": 0}) == 0
    # Testing that we can relax the Pmin of a profile resource by id
    assert temporal_curtailment(mock_scenario, pmin_by_id={3: 0}) == pytest.approx(0.1)
    curtailment = temporal_curtailment(mock_scenario, pmin_by_id={3: 0, 9: 0})
    assert curtailment == 0
    # Testing that we can override by-type with by-id
    curtailment = temporal_curtailment(
        mock_scenario, pmin_by_type={"hydro": 0}, pmin_by_id={9: None}
    )
    assert curtailment == pytest.approx(0.1)
