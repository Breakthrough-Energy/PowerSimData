import numpy as np
import pytest
from numpy.testing import assert_almost_equal

from powersimdata.input.change_table import ChangeTable
from powersimdata.input.grid import Grid
from powersimdata.input.input_data import InputData
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile

interconnect = ["Western"]
param = {
    "demand": "vJan2021",
    "hydro": "vJan2021",
    "solar": "vJan2021",
    "wind": "vJan2021",
    "n_zone_to_scale": 6,
    "n_plant_to_scale": 50,
    "n_plant_to_add": 100,
}
profile_type = {
    "wind": {"wind", "wind_offshore"},
    "solar": {"solar"},
    "hydro": {"hydro"},
    "demand": {"demand"},
}


def get_zone_with_resource(base_grid, resource):
    zone = base_grid.plant.groupby("type").get_group(resource)["zone_name"].unique()
    return zone


def get_plant_with_resource(base_grid, resource):
    plant_id = base_grid.plant.groupby("type").get_group(resource).index
    return plant_id


def get_change_table_for_zone_scaling(base_grid, resource):
    n_zone = param["n_zone_to_scale"]
    zones = get_zone_with_resource(base_grid, resource)

    ct = ChangeTable(base_grid)
    ct.scale_plant_capacity(
        resource,
        zone_name={
            z: f
            for z, f in zip(
                np.random.choice(zones, size=n_zone, replace=False),
                2 * np.random.random(size=n_zone),
            )
        },
    )
    return ct.ct


def get_change_table_for_id_scaling(base_grid, resource):
    n_plant = param["n_plant_to_scale"]
    plants = get_plant_with_resource(base_grid, resource)

    ct = ChangeTable(base_grid)
    ct.scale_plant_capacity(
        resource,
        plant_id={
            z: f
            for z, f in zip(
                np.random.choice(plants, size=n_plant, replace=False),
                2 * np.random.random(size=n_plant),
            )
        },
    )
    return ct.ct


def get_change_table_for_new_plant_addition(base_grid, resource):
    n_plant = param["n_plant_to_add"]
    new_plant_bus_id = np.random.choice(
        base_grid.bus.index, size=n_plant, replace=False
    )
    new_plant_pmax = 10 + 240 * np.random.random(size=n_plant)
    new_plant = []
    for b, p in zip(new_plant_bus_id, new_plant_pmax):
        new_plant.append({"type": resource, "bus_id": b, "Pmax": p})

    ct = ChangeTable(base_grid)
    ct.add_plant(new_plant)

    return ct.ct


def _check_plants_are_scaled(ct, base_grid, profile_info, raw_profile, resource):
    plant_id_type = get_plant_with_resource(base_grid, resource)

    base_profile = (
        raw_profile[plant_id_type] * base_grid.plant.loc[plant_id_type, "Pmax"]
    )

    tg = TransformGrid(base_grid, ct)
    transformed_grid = tg.get_grid()

    tp = TransformProfile(profile_info, transformed_grid, ct)
    transformed_profile = tp.get_profile(resource)

    scaled_plant_id = []
    scaling_factor_plant = []
    if "zone_id" in ct[resource].keys():
        for z, f in ct[resource]["zone_id"].items():
            plant_id_zone = (
                base_grid.plant.groupby(["zone_id", "type"])
                .get_group((z, resource))
                .index.tolist()
            )
            scaled_plant_id += plant_id_zone
            scaling_factor_plant += [f] * len(plant_id_zone)
    if "plant_id" in ct[resource].keys():
        for i, f in ct[resource]["plant_id"].items():
            if i in scaled_plant_id:
                scaling_factor_plant[scaled_plant_id.index(i)] *= f
            else:
                scaled_plant_id.append(i)
                scaling_factor_plant.append(f)

    assert not base_profile.equals(transformed_profile)
    assert_almost_equal(
        transformed_profile[scaled_plant_id].values,
        base_profile[scaled_plant_id].multiply(scaling_factor_plant, axis=1).values,
    )

    unscaled_plant_id = set(plant_id_type) - set(scaled_plant_id)
    if unscaled_plant_id:
        assert transformed_profile[unscaled_plant_id].equals(
            base_profile[unscaled_plant_id]
        )
    return transformed_profile


def _check_new_plants_are_added(ct, base_grid, profile_info, raw_profile, resource):
    n_plant = param["n_plant_to_add"]
    plant_id_type = (
        base_grid.plant.isin(profile_type[resource]).query("type == True").index
    )
    base_profile = (
        raw_profile[plant_id_type] * base_grid.plant.loc[plant_id_type, "Pmax"]
    )

    tg = TransformGrid(base_grid, ct)
    transformed_grid = tg.get_grid()

    tp = TransformProfile(profile_info, transformed_grid, ct)
    transformed_profile = tp.get_profile(resource)

    assert not transformed_profile.equals(base_profile)
    assert not len(base_profile.columns) == len(transformed_profile.columns)
    assert len(set(transformed_profile.columns) - set(base_profile.columns)) == n_plant
    assert set(transformed_profile.columns) - set(base_profile.columns) == set(
        transformed_grid.plant.index[-n_plant:]
    )

    return transformed_profile.drop(base_profile.columns, axis=1)


def _check_new_plants_are_not_scaled(base_grid, profile_info, raw_profile, resource):
    ct_zone = get_change_table_for_zone_scaling(base_grid, resource)
    ct_id = get_change_table_for_id_scaling(base_grid, resource)
    ct_new = get_change_table_for_new_plant_addition(base_grid, resource)
    ct = {**ct_zone, **ct_id[resource], **ct_new}
    # profile of new plants
    new_profile = _check_new_plants_are_added(
        ct_new, base_grid, profile_info, raw_profile, resource
    )
    # transformed profile
    scaled_profile = _check_plants_are_scaled(
        ct, base_grid, profile_info, raw_profile, resource
    )
    # check that the profiles of new plants in the scaled profile are not scaled
    assert new_profile.equals(scaled_profile[new_profile.columns])


def _check_profile_of_new_plants_are_produced_correctly(
    base_grid, profile_info, raw_profile, resource
):
    ct_new = get_change_table_for_new_plant_addition(base_grid, resource)
    new_profile = _check_new_plants_are_added(
        ct_new, base_grid, profile_info, raw_profile, resource
    )
    neighbor_id = [d["plant_id_neighbor"] for d in ct_new["new_plant"]]
    new_plant_pmax = [d["Pmax"] for d in ct_new["new_plant"]]

    for i, c in enumerate(new_profile.columns):
        neighbor_profile = raw_profile[neighbor_id[i]]
        assert new_profile[c].equals(neighbor_profile.multiply(new_plant_pmax[i]))


@pytest.fixture(scope="module")
def base_grid():
    grid = Grid(interconnect)
    return grid


def raw_profile(kind):
    input_data = InputData()
    grid_model = "test_usa_tamu"
    profile_info = {
        "grid_model": grid_model,
        f"base_{kind}": param[kind],
    }
    profile = input_data.get_data(profile_info, kind)
    return profile_info, profile


@pytest.fixture(scope="module")
def raw_hydro():
    return raw_profile("hydro")


@pytest.fixture(scope="module")
def raw_wind():
    return raw_profile("wind")


@pytest.fixture(scope="module")
def raw_solar():
    return raw_profile("solar")


@pytest.fixture(scope="module")
def raw_demand():
    return raw_profile("demand")


def test_demand_is_scaled(base_grid, raw_demand):
    demand_info, raw_demand = raw_demand
    base_demand = raw_demand[base_grid.id2zone.keys()]

    n_zone = param["n_zone_to_scale"]
    ct = ChangeTable(base_grid)
    ct.scale_demand(
        zone_id={
            z: f
            for z, f in zip(
                np.random.choice(
                    [i for i in base_grid.zone2id.values()], size=n_zone, replace=False
                ),
                2 * np.random.random(size=n_zone),
            )
        }
    )

    tg = TransformGrid(base_grid, ct.ct)
    transformed_grid = tg.get_grid()

    tp = TransformProfile(demand_info, transformed_grid, ct.ct)
    transformed_profile = tp.get_profile("demand")
    assert not base_demand.equals(transformed_profile)

    scaled_zone = list(ct.ct["demand"]["zone_id"].keys())
    unscaled_zone = set(base_grid.id2zone.keys()) - set(scaled_zone)
    factor = list(ct.ct["demand"]["zone_id"].values())
    assert transformed_profile[scaled_zone].equals(
        base_demand[scaled_zone].multiply(factor, axis=1)
    )
    if unscaled_zone:
        assert transformed_profile[unscaled_zone].equals(base_demand[unscaled_zone])


def test_solar_is_scaled_by_zone(base_grid, raw_solar):
    ct = get_change_table_for_zone_scaling(base_grid, "solar")
    _check_plants_are_scaled(ct, base_grid, *raw_solar, "solar")


def test_solar_is_scaled_by_id(base_grid, raw_solar):
    ct = get_change_table_for_id_scaling(base_grid, "solar")
    _check_plants_are_scaled(ct, base_grid, *raw_solar, "solar")


def test_solar_is_scaled_by_zone_and_id(base_grid, raw_solar):
    ct_zone = get_change_table_for_zone_scaling(base_grid, "solar")
    ct_id = get_change_table_for_id_scaling(base_grid, "solar")
    ct = {**ct_zone, **ct_id["solar"]}
    _check_plants_are_scaled(ct, base_grid, *raw_solar, "solar")


def test_wind_is_scaled_by_zone(base_grid, raw_wind):
    ct = get_change_table_for_zone_scaling(base_grid, "wind")
    _check_plants_are_scaled(ct, base_grid, *raw_wind, "wind")


def test_wind_is_scaled_by_id(base_grid, raw_wind):
    ct = get_change_table_for_id_scaling(base_grid, "wind")
    _check_plants_are_scaled(ct, base_grid, *raw_wind, "wind")


def test_wind_is_scaled_by_zone_and_id(base_grid, raw_wind):
    ct_zone = get_change_table_for_zone_scaling(base_grid, "wind")
    ct_id = get_change_table_for_id_scaling(base_grid, "wind")
    ct = {**ct_zone, **ct_id["wind"]}
    _check_plants_are_scaled(ct, base_grid, *raw_wind, "wind")


def test_hydro_is_scaled_by_zone(base_grid, raw_hydro):
    ct = get_change_table_for_zone_scaling(base_grid, "hydro")
    _check_plants_are_scaled(ct, base_grid, *raw_hydro, "hydro")


def test_hydro_is_scaled_by_id(base_grid, raw_hydro):
    ct = get_change_table_for_id_scaling(base_grid, "hydro")
    _check_plants_are_scaled(ct, base_grid, *raw_hydro, "hydro")


def test_hydro_is_scaled_by_zone_and_id(base_grid, raw_hydro):
    ct_zone = get_change_table_for_zone_scaling(base_grid, "hydro")
    ct_id = get_change_table_for_id_scaling(base_grid, "hydro")
    ct = {**ct_zone, **ct_id["hydro"]}
    _check_plants_are_scaled(ct, base_grid, *raw_hydro, "hydro")


def test_new_solar_are_added(base_grid, raw_solar):
    ct = get_change_table_for_new_plant_addition(base_grid, "solar")
    _ = _check_new_plants_are_added(ct, base_grid, *raw_solar, "solar")


def test_new_wind_are_added(base_grid, raw_wind):
    ct = get_change_table_for_new_plant_addition(base_grid, "wind")
    _ = _check_new_plants_are_added(ct, base_grid, *raw_wind, "wind")


def test_new_hydro_added(base_grid, raw_hydro):
    ct = get_change_table_for_new_plant_addition(base_grid, "hydro")
    _ = _check_new_plants_are_added(ct, base_grid, *raw_hydro, "hydro")


def test_new_solar_are_not_scaled(base_grid, raw_solar):
    _check_new_plants_are_not_scaled(base_grid, *raw_solar, "solar")


def test_new_wind_are_not_scaled(base_grid, raw_wind):
    _check_new_plants_are_not_scaled(base_grid, *raw_wind, "wind")


def test_new_hydro_are_not_scaled(base_grid, raw_hydro):
    _check_new_plants_are_not_scaled(base_grid, *raw_hydro, "hydro")


def test_new_solar_profile(base_grid, raw_solar):
    _check_profile_of_new_plants_are_produced_correctly(base_grid, *raw_solar, "solar")


def test_new_wind_profile(base_grid, raw_wind):
    _check_profile_of_new_plants_are_produced_correctly(base_grid, *raw_wind, "wind")


def test_new_hydro_profile(base_grid, raw_hydro):
    _check_profile_of_new_plants_are_produced_correctly(base_grid, *raw_hydro, "hydro")
