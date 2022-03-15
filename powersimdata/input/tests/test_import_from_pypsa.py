import pytest
from pandas.testing import assert_series_equal

from powersimdata.input.export_data import PYPSA_AVAILABLE, export_to_pypsa
from powersimdata.input.grid import Grid


@pytest.mark.skipif(not PYPSA_AVAILABLE, reason="Package PyPSA not available.")
def test_import_arbitrary_network_from_pypsa():
    import pypsa

    # TODO: How to deal with immutables and data_loc which is not in
    # powersimdata.grid.Grid.SUPPORTED_MODELS?

    # n = pypsa.examples.ac_dc_meshed()
    # grid = Grid(n)

    # assert not grid.bus.empty
    # assert len(n.buses) == len(grid.bus)


@pytest.mark.skipif(not PYPSA_AVAILABLE, reason="Package PyPSA not available.")
def test_import_exported_network():
    ref = Grid("Western")
    kwargs = dict(add_substations=True, add_load_shedding=False, add_all_columns=True)
    n = export_to_pypsa(ref, **kwargs)
    test = Grid(n)

    # TODO: Only the linear cost term is exported to pypsa
    for c in ["c0", "c2"]:
        test.gencost["before"][c] = ref.gencost["before"][c]
        test.gencost["after"][c] = ref.gencost["after"][c]

    # TODO: storages are not yet exported to pypsa
    test.storage = ref.storage

    # TODO: TransformerWinding is not translated to pypsa
    test.branch["branch_device_type"] = ref.branch.branch_device_type

    # Due to rounding errors we have to compare some columns in advance
    rtol = 1e-15
    assert_series_equal(ref.branch.x, test.branch.x, rtol=rtol)
    assert_series_equal(ref.branch.r, test.branch.r, rtol=rtol)
    assert_series_equal(ref.bus.Va, test.bus.Va, rtol=rtol)

    test.branch.x = ref.branch.x
    test.branch.r = ref.branch.r
    test.bus.Va = ref.bus.Va

    assert ref == test
