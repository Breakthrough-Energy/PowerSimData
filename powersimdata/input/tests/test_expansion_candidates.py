import pandas as pd
import pytest

from powersimdata.input.expansion_candidates import (
    ExpansionCandidates,
    check_branch_voltage,
    check_bus_id,
)
from powersimdata.input.grid import Grid

grid = Grid("Texas")


def test_column_types():
    ec = ExpansionCandidates(grid)
    with pytest.raises(TypeError):
        branch = {"branch_id": [1, 2]}
        ec.set_branch(branch)
    with pytest.raises(ValueError):
        plant = pd.DataFrame({"plant_id": [42]})
        ec.set_plant(plant)
    with pytest.raises(ValueError):
        storage = pd.DataFrame({"bus_id": [1, 2], "foo": [3, 4]})
        ec.set_storage(storage)


def test_check_branch_voltage():
    # baseKV = 230
    branch = pd.DataFrame({"from_bus": [3001004], "to_bus": [3008159]})
    check_branch_voltage(branch, grid)

    # baseKV = 115, 230
    branch = pd.DataFrame({"from_bus": [3001001], "to_bus": [3008156]})
    with pytest.raises(ValueError):
        check_branch_voltage(branch, grid)


def test_check_bus_id():
    bus_id = pd.Series([3001001])
    check_bus_id(bus_id, grid)

    with pytest.raises(ValueError):
        check_bus_id(bus_id, Grid("Western"))

    bus_id = pd.Series([-1])
    with pytest.raises(ValueError):
        check_bus_id(bus_id, grid)


def test_set_candidates():
    ec = ExpansionCandidates(grid)
    branch = grid.branch.head().loc[:, ["from_bus_id", "to_bus_id"]]
    branch = branch.rename(
        columns={
            "from_bus_id": "from_bus",
            "to_bus_id": "to_bus",
        }
    )
    ec.set_branch(branch)

    plant = grid.plant.head().loc[:, ["bus_id", "type"]]
    plant["marginal_cost"] = 4
    ec.set_plant(plant)

    storage = plant.loc[:, ["bus_id"]].copy()
    ec.set_storage(storage)
