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
        branch = pd.DataFrame()
        ec.set_branch(branch)


def test_check_branch_voltage():
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

    storage = grid.bus.head().reset_index().loc[:, ["bus_id"]]
    ec.set_storage(storage)
