import numpy as np
import pytest

from powersimdata.input.input_data import InputData
from powersimdata.utility.transfer_data import setup_server_connection
from powersimdata.input.change_table import ChangeTable
from powersimdata.input.grid import Grid
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile

interconnect = ["Western"]
param = {
    "Western": {
        "demand": "v4",
        "hydro": "v2",
        "solar": "v4.1",
        "wind": "v5.2",
        "n_zone_to_scale": 6,
        "n_plant_to_scale": 50,
        "n_plant_to_add": 100,
    }
}


def get_zone_with_resource(base_grid, resource):
    zone = list(
        base_grid.plant.groupby("type").get_group(resource)["zone_name"].unique()
    )
    return zone


def get_plant_with_resource(base_grid, resource):
    plant_id = list(base_grid.plant.groupby("type").get_group(resource).index)
    return plant_id


def get_change_table_for_zone_scaling(base_grid, resource):
    n_zone = param["_".join(interconnect)]["n_zone_to_scale"]
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
    n_plant = param["_".join(interconnect)]["n_plant_to_scale"]
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
    n_plant = param["_".join(interconnect)]["n_plant_to_add"]
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


def _check_plants_are_scaled(
    ssh_client, ct, base_grid, base_profile_resource, resource
):
    profile_info = base_profile_resource[0]
    base_profile = base_profile_resource[1]

    tg = TransformGrid(base_grid, ct)
    transformed_grid = tg.get_grid()

    tp = TransformProfile(ssh_client, profile_info, transformed_grid, ct)
    transformed_profile = tp.get_profile(resource)

    scaled_plant_id = []
    scaling_factor_plant = []
    if "zone_id" in ct[resource].keys():
        scaled_zone = list(ct[resource]["zone_id"].keys())
        scaling_factor_for_zone = list(ct[resource]["zone_id"].values())
        for z, f in zip(scaled_zone, scaling_factor_for_zone):
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
    assert transformed_profile[scaled_plant_id].equals(
        base_profile[scaled_plant_id].multiply(scaling_factor_plant, axis=1)
    )

    all_plant_id = base_grid.plant.groupby("type").get_group(resource).index.tolist()
    unscaled_plant_id = set(all_plant_id) - set(scaled_plant_id)
    if unscaled_plant_id:
        assert transformed_profile[unscaled_plant_id].equals(
            base_profile[unscaled_plant_id]
        )
    return transformed_profile


def _check_new_plants_are_added(
    ssh_client, ct, base_grid, base_profile_resource, resource
):
    n_plant = param["_".join(interconnect)]["n_plant_to_add"]
    profile_info = base_profile_resource[0]
    base_profile = base_profile_resource[1]

    tg = TransformGrid(base_grid, ct)
    transformed_grid = tg.get_grid()

    tp = TransformProfile(ssh_client, profile_info, transformed_grid, ct)
    transformed_profile = tp.get_profile(resource)

    assert not transformed_profile.equals(base_profile)
    assert not len(base_profile.columns) == len(transformed_profile.columns)
    assert len(set(transformed_profile.columns) - set(base_profile.columns)) == n_plant
    assert set(transformed_profile.columns) - set(base_profile.columns) == set(
        transformed_grid.plant.index[-n_plant:]
    )

    return transformed_profile.drop(base_profile.columns, axis=1)


def _check_new_plants_are_not_scaled(
    ssh_client, base_grid, base_profile_resource, resource
):
    ct_zone = get_change_table_for_zone_scaling(base_grid, resource)
    ct_id = get_change_table_for_id_scaling(base_grid, resource)
    ct_new = get_change_table_for_new_plant_addition(base_grid, resource)
    ct = {**ct_zone, **ct_id[resource], **ct_new}
    # profile of new plants
    new_profile = _check_new_plants_are_added(
        ssh_client, ct_new, base_grid, base_profile_resource, resource
    )
    # transformed profile
    scaled_profile = _check_plants_are_scaled(
        ssh_client, ct, base_grid, base_profile_resource, resource
    )
    # check that the profiles of new plants in the scaled profile are not scaled
    assert new_profile.equals(scaled_profile[new_profile.columns])


def _check_profile_of_new_plants_are_produced_correctly(
    base_grid, base_profile_resource, resource
):
    ct_new = get_change_table_for_new_plant_addition(base_grid, resource)
    new_profile = _check_new_plants_are_added(
        ssh_client, ct_new, base_grid, base_profile_resource, resource
    )
    neighbor_id = [d["plant_id_neighbor"] for d in ct_new["new_plant"]]
    neighbor_pmax = base_grid.plant.loc[neighbor_id].Pmax.to_list()
    new_plant_pmax = [d["Pmax"] for d in ct_new["new_plant"]]

    for i, c in enumerate(new_profile.columns):
        neighbor_profile = base_profile_resource[1][neighbor_id[i]]
        assert new_profile[c].equals(
            neighbor_profile.multiply(new_plant_pmax[i] / neighbor_pmax[i])
        )


@pytest.fixture(scope="module")
def ssh_client():
    ssh_client = setup_server_connection()
    yield ssh_client
    ssh_client.close()


@pytest.fixture(scope="module")
def base_grid():
    grid = Grid(interconnect)
    return grid


@pytest.fixture(scope="module")
def base_hydro(ssh_client):
    input_data = InputData(ssh_client)
    profile_info = {
        "interconnect": "_".join(interconnect),
        "base_hydro": param["_".join(interconnect)]["hydro"],
    }
    profile = input_data.get_data(profile_info, "hydro")
    return profile_info, profile


@pytest.fixture(scope="module")
def base_wind(ssh_client):
    input_data = InputData(ssh_client)
    profile_info = {
        "interconnect": "_".join(interconnect),
        "base_wind": param["_".join(interconnect)]["wind"],
    }
    profile = input_data.get_data(profile_info, "wind")
    return profile_info, profile


@pytest.fixture(scope="module")
def base_solar(ssh_client):
    input_data = InputData(ssh_client)
    profile_info = {
        "interconnect": "_".join(interconnect),
        "base_solar": param["_".join(interconnect)]["solar"],
    }
    profile = input_data.get_data(profile_info, "solar")
    return profile_info, profile


@pytest.fixture(scope="module")
def base_demand(ssh_client):
    input_data = InputData(ssh_client)
    profile_info = {
        "interconnect": "_".join(interconnect),
        "base_demand": param["_".join(interconnect)]["demand"],
    }
    profile = input_data.get_data(profile_info, "demand")
    return profile_info, profile


@pytest.mark.integration
def test_demand_is_scaled(ssh_client, base_grid, base_demand):
    n_zone = param["_".join(interconnect)]["n_zone_to_scale"]
    profile_info = base_demand[0]
    base_profile = base_demand[1]

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

    tp = TransformProfile(ssh_client, profile_info, base_grid, ct.ct)
    transformed_profile = tp.get_profile("demand")
    assert not base_profile.equals(transformed_profile)

    scaled_zone = list(ct.ct["demand"]["zone_id"].keys())
    unscaled_zone = set(base_grid.id2zone.keys()) - set(scaled_zone)
    factor = list(ct.ct["demand"]["zone_id"].values())
    assert transformed_profile[scaled_zone].equals(
        base_profile[scaled_zone].multiply(factor, axis=1)
    )
    if unscaled_zone:
        assert transformed_profile[unscaled_zone].equals(base_profile[unscaled_zone])


@pytest.mark.integration
def test_solar_is_scaled_by_zone(ssh_client, base_grid, base_solar):
    ct = get_change_table_for_zone_scaling(base_grid, "solar")
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_solar, "solar")


@pytest.mark.integration
def test_solar_is_scaled_by_id(ssh_client, base_grid, base_solar):
    ct = get_change_table_for_id_scaling(base_grid, "solar")
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_solar, "solar")


@pytest.mark.integration
def test_solar_is_scaled_by_zone_and_id(ssh_client, base_grid, base_solar):
    ct_zone = get_change_table_for_zone_scaling(base_grid, "solar")
    ct_id = get_change_table_for_id_scaling(base_grid, "solar")
    ct = {**ct_zone, **ct_id["solar"]}
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_solar, "solar")


@pytest.mark.integration
def test_wind_is_scaled_by_zone(ssh_client, base_grid, base_wind):
    ct = get_change_table_for_zone_scaling(base_grid, "wind")
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_wind, "wind")


@pytest.mark.integration
def test_wind_is_scaled_by_id(ssh_client, base_grid, base_wind):
    ct = get_change_table_for_id_scaling(base_grid, "wind")
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_wind, "wind")


@pytest.mark.integration
def test_wind_is_scaled_by_zone_and_id(ssh_client, base_grid, base_wind):
    ct_zone = get_change_table_for_zone_scaling(base_grid, "wind")
    ct_id = get_change_table_for_id_scaling(base_grid, "wind")
    ct = {**ct_zone, **ct_id["wind"]}
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_wind, "wind")


@pytest.mark.integration
def test_hydro_is_scaled_by_zone(ssh_client, base_grid, base_hydro):
    ct = get_change_table_for_zone_scaling(base_grid, "hydro")
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_hydro, "hydro")


@pytest.mark.integration
def test_hydro_is_scaled_by_id(ssh_client, base_grid, base_hydro):
    ct = get_change_table_for_id_scaling(base_grid, "hydro")
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_hydro, "hydro")


@pytest.mark.integration
def test_hydro_is_scaled_by_zone_and_id(ssh_client, base_grid, base_hydro):
    ct_zone = get_change_table_for_zone_scaling(base_grid, "hydro")
    ct_id = get_change_table_for_id_scaling(base_grid, "hydro")
    ct = {**ct_zone, **ct_id["hydro"]}
    _ = _check_plants_are_scaled(ssh_client, ct, base_grid, base_hydro, "hydro")


@pytest.mark.integration
def test_new_solar_are_added(ssh_client, base_grid, base_solar):
    ct = get_change_table_for_new_plant_addition(base_grid, "solar")
    _ = _check_new_plants_are_added(ssh_client, ct, base_grid, base_solar, "solar")


@pytest.mark.integration
def test_new_wind_are_added(ssh_client, base_grid, base_wind):
    ct = get_change_table_for_new_plant_addition(base_grid, "wind")
    _ = _check_new_plants_are_added(ssh_client, ct, base_grid, base_wind, "wind")


@pytest.mark.integration
def test_new_hydro_added(ssh_client, base_grid, base_hydro):
    ct = get_change_table_for_new_plant_addition(base_grid, "hydro")
    _ = _check_new_plants_are_added(ssh_client, ct, base_grid, base_hydro, "hydro")


@pytest.mark.integration
def test_new_solar_are_not_scaled(ssh_client, base_grid, base_solar):
    _check_new_plants_are_not_scaled(ssh_client, base_grid, base_solar, "solar")


@pytest.mark.integration
def test_new_wind_are_not_scaled(ssh_client, base_grid, base_wind):
    _check_new_plants_are_not_scaled(ssh_client, base_grid, base_wind, "wind")


@pytest.mark.integration
def test_new_hydro_are_not_scaled(ssh_client, base_grid, base_hydro):
    _check_new_plants_are_not_scaled(ssh_client, base_grid, base_hydro, "hydro")


@pytest.mark.integration
def test_new_solar_profile(base_grid, base_solar):
    _check_profile_of_new_plants_are_produced_correctly(base_grid, base_solar, "solar")


@pytest.mark.integration
def test_new_wind_profile(base_grid, base_wind):
    _check_profile_of_new_plants_are_produced_correctly(base_grid, base_wind, "wind")


@pytest.mark.integration
def test_new_hydro_profile(base_grid, base_hydro):
    _check_profile_of_new_plants_are_produced_correctly(base_grid, base_hydro, "hydro")
