from importlib.util import find_spec

import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from powersimdata.input.converter.pypsa_to_grid import FromPyPSA
from powersimdata.input.exporter.export_to_pypsa import export_to_pypsa
from powersimdata.input.grid import Grid


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_import_arbitrary_network_from_pypsa_to_grid():
    import pypsa

    n = pypsa.examples.ac_dc_meshed()
    grid = FromPyPSA(n)

    assert not grid.bus.empty
    assert len(n.buses) == len(grid.bus)


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_import_network_including_storages_from_pypsa_to_grid():
    import pypsa

    n = pypsa.examples.storage_hvdc()
    grid = FromPyPSA(n)

    assert not grid.bus.empty
    assert len(n.buses) == len(grid.bus)
    assert not grid.storage["gen"].empty
    assert not grid.storage["gencost"].empty
    assert not grid.storage["StorageData"].empty


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_import_exported_network():

    ref = Grid("Western")
    kwargs = dict(add_substations=True, add_load_shedding=False, add_all_columns=False)
    n = export_to_pypsa(ref, **kwargs)
    test = FromPyPSA(n, add_pypsa_cols=False)

    # Only a scaled version of linear cost term is exported to pypsa
    # Test whether the exported marginal cost is in the same order of magnitude
    ref_total_c1 = ref.gencost["before"]["c1"].sum()
    test_total_c1 = test.gencost["before"]["c1"].sum()
    assert ref_total_c1 / test_total_c1 > 0.95 and ref_total_c1 / test_total_c1 < 1.05

    # Due to rounding errors we have to compare some columns in advance
    rtol = 1e-15
    assert_series_equal(ref.branch.x, test.branch.x, rtol=rtol)
    assert_series_equal(ref.branch.r, test.branch.r, rtol=rtol)
    assert_series_equal(ref.bus.Va, test.bus.Va, rtol=rtol)

    test.branch.x = ref.branch.x
    test.branch.r = ref.branch.r
    test.bus.Va = ref.bus.Va

    print("Difference in bus columns")
    print(ref.bus.columns)
    print(test.bus.columns)

    print("Difference in branch columns")
    print(ref.branch.columns)
    print(test.branch.columns)

    assert_frame_equal(ref.bus[ref.bus.columns], test.bus[ref.bus.columns])

    assert ref == test
