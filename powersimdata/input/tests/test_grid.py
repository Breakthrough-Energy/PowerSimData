import copy

import pytest

from powersimdata.input.grid import Grid

INCORRECT_SOURCE = "invalid_source"
INCORRECT_ENGINE = "invalid_engine"


def test_grid_incorrect_source():
    with pytest.raises(ValueError):
        Grid(["USA"], source=INCORRECT_SOURCE)


def test_grid_incorrect_engine():
    with pytest.raises(ValueError):
        Grid(["USA"], engine=INCORRECT_ENGINE)


def test_grid_type():
    g = Grid(["USA"])
    assert isinstance(g, Grid)


@pytest.fixture(scope="session")
def base_texas():
    return Grid(["Texas"])


@pytest.fixture(scope="session")
def base_western():
    return Grid(["Western"])


def test_deepcopy_works(base_texas):
    assert isinstance(copy.deepcopy(base_texas), Grid)


def test_grid_eq_success_simple(base_texas):
    assert base_texas == Grid(["Texas"])


def test_grid_eq_failure_simple(base_texas, base_western):
    assert base_texas != base_western


def test_grid_eq_failure_bus(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.bus.loc[test_grid.bus.head(1).index, "baseKV"] *= 2
    assert base_texas != test_grid


def test_grid_eq_success_bus_type(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.bus.type = 1
    assert base_texas == test_grid


def test_grid_eq_failure_branch(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.branch.loc[test_grid.branch.head(1).index, "rateA"] *= 2
    assert base_texas != test_grid


def test_grid_eq_failure_dcline(base_western):
    test_grid = copy.deepcopy(base_western)
    test_grid.dcline.loc[test_grid.dcline.head(1).index, "Pmax"] *= 2
    assert base_western != test_grid


def test_grid_eq_failure_gencost_before(base_texas):
    test_grid = copy.deepcopy(base_texas)
    before = test_grid.gencost["before"]
    before.loc[before.head(1).index, "n"] += 1
    assert base_texas != test_grid


def test_grid_eq_success_gencost_after(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.gencost["after"] = test_grid.gencost["after"].drop(
        test_grid.gencost["after"].tail(1).index
    )
    assert base_texas == test_grid


def test_grid_eq_failure_plant(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.plant.loc[test_grid.plant.head(1).index, "Pmax"] *= 2
    assert base_texas != test_grid


def test_grid_eq_success_plant_ramp30(base_texas):
    test_grid = copy.deepcopy(base_texas)
    test_grid.plant.loc[test_grid.plant.head(1).index, "ramp_30"] *= 2
    assert base_texas == test_grid


def test_grid_eq_failure_sub(base_texas):
    test_grid = copy.deepcopy(base_texas)
    first_name = str(test_grid.sub.loc[test_grid.sub.head(1).index, "name"])
    test_grid.sub.loc[test_grid.sub.head(1).index, "name"] = first_name[::-1]
    assert base_texas != test_grid


def test_grid_eq_failure_storage(base_texas):
    test_grid = copy.deepcopy(base_texas)
    gencost = {g: 0 for g in test_grid.storage["gencost"].columns}
    gen = {g: 0 for g in test_grid.storage["gen"].columns}
    test_grid.storage["gencost"].loc[0, :] = gencost
    test_grid.storage["gen"].loc[0, :] = gen
    assert base_texas != test_grid


def test_that_fields_are_not_modified_when_loading_another_grid():
    western_grid = Grid(["Western"])
    western_plant_original_shape = western_grid.plant.shape
    Grid(["Eastern"])
    assert western_plant_original_shape == western_grid.plant.shape
