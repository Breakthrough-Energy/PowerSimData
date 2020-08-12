import numpy as np
import pytest

from powersimdata.input.input_data import InputData
from powersimdata.utility.transfer_data import setup_server_connection
from powersimdata.input.change_table import ChangeTable
from powersimdata.input.grid import Grid
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.scenario.helpers import interconnect2name

interconnect = ["Western"]


def get_zone_with_resource(base_grid, resource):
    zone = []
    for z in base_grid.zone2id.keys():
        try:
            base_grid.plant.groupby(["zone_name", "type"]).get_group((z, resource))
            zone.append(z)
        except KeyError:
            pass
    return zone


def get_plant_with_resource(base_grid, resource):
    plant_id = []
    for i in interconnect:
        try:
            plant_id_interconnect = (
                base_grid.plant.groupby(["interconnect", "type"])
                .get_group((i, resource))
                .index.to_list()
            )
            plant_id += plant_id_interconnect
        except KeyError:
            pass
    return plant_id


def is_renewable_profile_scaled(
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


def are_renewable_added(ssh_client, base_grid, base_profile_resource, resource):
    n_plant = 100
    profile_info = base_profile_resource[0]
    base_profile = base_profile_resource[1]
    new_plant_bus_id = np.random.choice(
        base_grid.bus.index, size=n_plant, replace=False
    )
    new_plant_pmax = 10 + 240 * np.random.random(size=n_plant)
    new_plant = []
    for b, p in zip(new_plant_bus_id, new_plant_pmax):
        new_plant.append({"type": resource, "bus_id": b, "Pmax": p})

    ct = ChangeTable(base_grid)
    ct.add_plant(new_plant)

    tg = TransformGrid(base_grid, ct.ct)
    transformed_grid = tg.get_grid()

    tp = TransformProfile(ssh_client, profile_info, transformed_grid, ct.ct)
    transformed_profile = tp.get_profile(resource)

    assert not transformed_profile.equals(base_profile)
    assert not len(base_profile.columns) == len(transformed_profile.columns)
    assert len(set(transformed_profile.columns) - set(base_profile.columns)) == n_plant
    assert set(transformed_profile.columns) - set(base_profile.columns) == set(
        transformed_grid.plant.index[-n_plant:]
    )
    assert base_profile.equals(
        transformed_profile.drop(transformed_grid.plant.index[-n_plant:], axis=1)
    )
    ct.clear()


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
    profile_info = {"interconnect": "_".join(interconnect), "base_hydro": "v2"}
    profile = input_data.get_data(profile_info, "hydro")
    return profile_info, profile


@pytest.fixture(scope="module")
def base_wind(ssh_client):
    input_data = InputData(ssh_client)
    profile_info = {"interconnect": "_".join(interconnect), "base_wind": "v5.2"}
    profile = input_data.get_data(profile_info, "wind")
    return profile_info, profile


@pytest.fixture(scope="module")
def base_solar(ssh_client):
    input_data = InputData(ssh_client)
    profile_info = {"interconnect": "_".join(interconnect), "base_solar": "v4.1"}
    profile = input_data.get_data(profile_info, "solar")
    return profile_info, profile


@pytest.fixture(scope="module")
def base_demand(ssh_client):
    input_data = InputData(ssh_client)
    profile_info = {"interconnect": "_".join(interconnect), "base_demand": "v4"}
    profile = input_data.get_data(profile_info, "demand")
    return profile_info, profile


@pytest.mark.integration
def test_demand_is_scaled(ssh_client, base_grid, base_demand):
    n_zone = 8
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
    n_zone = 6
    zone_with_solar = get_zone_with_resource(base_grid, "solar")

    ct = ChangeTable(base_grid)
    ct.scale_plant_capacity(
        "solar",
        zone_name={
            z: f
            for z, f in zip(
                np.random.choice(zone_with_solar, size=n_zone, replace=False),
                2 * np.random.random(size=n_zone),
            )
        },
    )
    is_renewable_profile_scaled(ssh_client, ct.ct, base_grid, base_solar, "solar")


@pytest.mark.integration
def test_wind_is_scaled_by_zone(ssh_client, base_grid, base_wind):
    n_zone = 6
    zone_with_solar = get_zone_with_resource(base_grid, "wind")

    ct = ChangeTable(base_grid)
    ct.scale_plant_capacity(
        "wind",
        zone_name={
            z: f
            for z, f in zip(
                np.random.choice(zone_with_solar, size=n_zone, replace=False),
                2 * np.random.random(size=n_zone),
            )
        },
    )
    is_renewable_profile_scaled(ssh_client, ct.ct, base_grid, base_wind, "wind")


@pytest.mark.integration
def test_hydro_is_scaled_by_zone(ssh_client, base_grid, base_hydro):
    n_zone = 6
    zone_with_solar = get_zone_with_resource(base_grid, "hydro")

    ct = ChangeTable(base_grid)
    ct.scale_plant_capacity(
        "hydro",
        zone_name={
            z: f
            for z, f in zip(
                np.random.choice(zone_with_solar, size=n_zone, replace=False),
                2 * np.random.random(size=n_zone),
            )
        },
    )
    is_renewable_profile_scaled(ssh_client, ct.ct, base_grid, base_hydro, "hydro")


@pytest.mark.integration
def test_add_solar(ssh_client, base_grid, base_solar):
    are_renewable_added(ssh_client, base_grid, base_solar, "solar")


@pytest.mark.integration
def test_add_hydro(ssh_client, base_grid, base_hydro):
    are_renewable_added(ssh_client, base_grid, base_hydro, "hydro")


@pytest.mark.integration
def test_add_wind(ssh_client, base_grid, base_wind):
    are_renewable_added(ssh_client, base_grid, base_wind, "wind")
