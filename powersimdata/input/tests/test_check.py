import pytest

from powersimdata import Grid
from powersimdata.input.check import check_grid


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
