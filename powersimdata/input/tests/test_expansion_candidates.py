import pandas as pd
import pytest

from powersimdata.input.expansion_candidates import ExpansionCandidates, check_branch
from powersimdata.input.grid import Grid


def test_column_types():
    grid = Grid("Texas")
    ec = ExpansionCandidates(grid)
    with pytest.raises(TypeError):
        branch = pd.DataFrame()
        ec.set_branch(branch)


def test_check_branch():
    grid = Grid("Texas")
    branch = pd.DataFrame({"from_bus": [3001001], "to_bus": [3008156]})
    with pytest.raises(ValueError):
        check_branch(branch, grid)
