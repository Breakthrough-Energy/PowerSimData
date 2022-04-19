import pytest

from powersimdata.input.export_data import PYPSA_AVAILABLE, export_to_pypsa
from powersimdata.input.grid import Grid


def assert_columns_preserved(n):
    assert "Vmax" in n.buses
    assert "ramp_10" in n.generators
    assert "rateB" in n.lines
    assert "QminF" in n.links


def assert_columns_deleted(n):
    assert "Vmax" not in n.buses
    assert "ramp_10" not in n.generators
    assert "rateB" not in n.lines
    assert "QminF" not in n.links


@pytest.mark.skipif(not PYPSA_AVAILABLE, reason="Package PyPSA not available.")
def test_export_grid_to_pypsa():
    grid = Grid("USA")

    n = export_to_pypsa(grid, add_substations=False)
    assert len(n.snapshots) == 1
    assert not n.loads_t.p.empty
    assert not n.generators_t.p.empty
    assert len(n.buses) == len(grid.bus)
    assert_columns_deleted(n)

    n = export_to_pypsa(grid, add_all_columns=True, add_substations=False)
    assert len(n.snapshots) == 1
    assert not n.loads_t.p.empty
    assert not n.generators_t.p.empty
    assert len(n.buses) == len(grid.bus)
    assert_columns_preserved(n)

    n = export_to_pypsa(grid, add_substations=True)
    assert len(n.buses) == len(grid.sub) + len(grid.bus)
