import pytest

from powersimdata import Grid
from powersimdata.input.check import check_grid


def test_error_handling():
    grid = Grid("Western")
    del grid.dcline
    with pytest.raises(ValueError):
        check_grid(grid)


def test_check_eastern():
    grid = Grid("Eastern")
    check_grid(grid)


def test_check_western():
    grid = Grid("Western")
    check_grid(grid)


def test_check_texas():
    grid = Grid("Texas")
    check_grid(grid)


def test_check_western_texas():
    grid = Grid(["Western", "Texas"])
    check_grid(grid)


def test_check_usa():
    grid = Grid(["USA"])
    check_grid(grid)
