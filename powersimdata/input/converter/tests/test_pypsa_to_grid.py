import pypsa
from pandas.testing import assert_series_equal

from powersimdata.input.change_table import ChangeTable
from powersimdata.input.converter.pypsa_to_grid import FromPyPSA
from powersimdata.input.exporter.export_to_pypsa import export_to_pypsa
from powersimdata.input.grid import Grid
from powersimdata.input.transform_grid import TransformGrid


def test_import_arbitrary_network_from_pypsa_to_grid():

    n = pypsa.examples.ac_dc_meshed()
    grid = FromPyPSA(n).build()

    assert not grid.bus.empty
    assert len(n.buses) == len(grid.bus)


def test_import_network_including_storages_from_pypsa_to_grid():

    n = pypsa.examples.storage_hvdc()
    grid = FromPyPSA(n).build()

    inflow = n.get_switchable_as_dense("StorageUnit", "inflow")
    has_inflow = inflow.any()

    assert not grid.bus.empty
    assert len(n.buses) + has_inflow.sum() == len(grid.bus)
    assert len(n.generators) + has_inflow.sum() == len(grid.plant)
    assert all(
        [
            "inflow" in i
            for i in grid.plant.iloc[len(grid.plant) - has_inflow.sum() :].index
        ]
    )
    assert not grid.storage["gen"].empty
    assert not grid.storage["gencost"].empty
    assert not grid.storage["StorageData"].empty


def test_import_exported_network():

    grid = Grid("Western")
    ct = ChangeTable(grid)
    storage = [
        {"bus_id": 2021005, "capacity": 116.0},
        {"bus_id": 2028827, "capacity": 82.5},
        {"bus_id": 2028060, "capacity": 82.5},
    ]
    ct.add_storage_capacity(storage)
    ref = TransformGrid(grid, ct.ct).get_grid()

    kwargs = dict(add_substations=True, add_load_shedding=False, add_all_columns=True)
    n = export_to_pypsa(ref, **kwargs)
    test = Grid(
        "Western",
        source="pypsa",
        grid_model="usa_tamu",
        network=n,
        add_pypsa_cols=False,
    )

    # Only a scaled version of linear cost term is exported to pypsa
    # Test whether the exported marginal cost is in the same order of magnitude
    ref_total_c1 = ref.gencost["before"]["c1"].sum()
    test_total_c1 = test.gencost["before"]["c1"].sum()
    assert ref_total_c1 / test_total_c1 > 0.95 and ref_total_c1 / test_total_c1 < 1.05

    # Now overwrite costs
    for c in ["c0", "c1", "c2"]:
        test.gencost["before"][c] = ref.gencost["before"][c]
        test.gencost["after"][c] = ref.gencost["after"][c]

    # Due to rounding errors we have to compare some columns in advance
    rtol = 1e-15
    assert_series_equal(ref.branch.x, test.branch.x, rtol=rtol)
    assert_series_equal(ref.branch.r, test.branch.r, rtol=rtol)
    assert_series_equal(ref.bus.Va, test.bus.Va, rtol=rtol)

    test.branch.x = ref.branch.x
    test.branch.r = ref.branch.r
    test.bus.Va = ref.bus.Va

    # storage specification is need in import but has to removed for testing
    test.storage["gencost"].drop(columns="pypsa_component", inplace=True)
    test.storage["gen"].drop(columns="pypsa_component", inplace=True)
    test.storage["StorageData"].drop(columns="pypsa_component", inplace=True)

    assert ref == test
