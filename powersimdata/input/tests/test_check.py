import pytest

from powersimdata import Grid
from powersimdata.input.check import _check_grid_models_match, check_grid


def test_error_handling():
    grid = Grid("Western")
    del grid.dcline
    with pytest.raises(ValueError):
        check_grid(grid)


@pytest.mark.parametrize(
    "interconnect", ["Eastern", "Western", "Texas", ["Western", "Texas"], "USA"]
)
def test_check_grid(interconnect):
    grid = Grid(interconnect)
    check_grid(grid)


def check_grid_models_match_success():
    _check_grid_models_match(Grid("Western"), Grid("Texas"))


def check_grid_models_match_failure():
    grid1 = Grid("Western")
    grid2 = Grid("Texas")
    grid2.grid_model == "foo"
    with pytest.raises(ValueError):
        _check_grid_models_match(grid1, grid2)
