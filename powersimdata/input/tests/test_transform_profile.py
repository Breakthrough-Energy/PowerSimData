import pytest

from powersimdata.input.profiles import InputData
from powersimdata.utility.transfer_data import setup_server_connection
from powersimdata.input.change_table import ChangeTable
from powersimdata.scenario.scenario import Scenario
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile


scenario_id = "564"


def is_renewable_profile_scaled(name, grid, ct, base_profile, scaled_profile):
    if name in ct.keys():
        scaled_plant_id = []
        scaling_factor_plant = []
        if "zone_id" in ct[name].keys():
            scaled_zone = list(ct[name]["zone_id"].keys())
            scaling_factor_for_zone = list(ct[name]["zone_id"].values())
            for z, f in zip(scaled_zone, scaling_factor_for_zone):
                plant_id_zone = (
                    grid.plant.groupby(["zone_id", "type"])
                    .get_group((z, name))
                    .index.tolist()
                )
                scaled_plant_id += plant_id_zone
                scaling_factor_plant += [f] * len(plant_id_zone)
        if "plant_id" in ct[name].keys():
            for i, f in ct[name]["plant_id"].items():
                if i in scaled_plant_id:
                    scaling_factor_plant[scaled_plant_id.index(i)] *= f
                else:
                    scaled_plant_id.append(i)
                    scaling_factor_plant.append(f)
        assert scaled_profile[scaled_plant_id].equals(
            base_profile[scaled_plant_id].multiply(scaling_factor_plant, axis=1)
        )

        all_plant_id = grid.plant.groupby("type").get_group(name).index.tolist()
        unscaled_plant_id = set(all_plant_id) - set(scaled_plant_id)
        if unscaled_plant_id:
            assert scaled_profile[unscaled_plant_id].equals(
                base_profile[unscaled_plant_id]
            )


@pytest.fixture(scope="module")
def scenario():
    return Scenario(scenario_id)


@pytest.fixture(scope="module")
def base_hydro(scenario):
    ssh_client = setup_server_connection()
    input_data = InputData(ssh_client)
    base_hydro = input_data.get_data(scenario.info, "hydro")
    ssh_client.close()
    return base_hydro


@pytest.fixture(scope="module")
def base_wind(scenario):
    ssh_client = setup_server_connection()
    input_data = InputData(ssh_client)
    base_wind = input_data.get_data(scenario.info, "wind")
    ssh_client.close()
    return base_wind


@pytest.fixture(scope="module")
def base_solar(scenario):
    ssh_client = setup_server_connection()
    input_data = InputData(ssh_client)
    base_solar = input_data.get_data(scenario.info, "solar")
    ssh_client.close()
    return base_solar


@pytest.fixture(scope="module")
def base_demand(scenario):
    print(scenario.info)
    ssh_client = setup_server_connection()
    input_data = InputData(ssh_client)
    base_demand = input_data.get_data(scenario.info, "demand")
    ssh_client.close()
    return base_demand


@pytest.mark.integration
def test_demand_is_scaled(scenario, base_demand):
    tp = TransformProfile(
        scenario.ssh, scenario.info, scenario.state.get_grid(), scenario.state.get_ct()
    )
    scaled_demand = tp.get_demand()
    assert not base_demand.equals(scaled_demand)

    ct = scenario.state.get_ct()
    grid = scenario.state.get_grid()
    if "demand" in ct.keys():
        scaled_zone = list(ct["demand"]["zone_id"].keys())
        unscaled_zone = set(grid.id2zone.keys()) - set(scaled_zone)
        factor = list(ct["demand"]["zone_id"].values())
        assert scaled_demand[scaled_zone].equals(
            base_demand[scaled_zone].multiply(factor, axis=1)
        )
        if unscaled_zone:
            assert scaled_demand[unscaled_zone].equals(base_demand[unscaled_zone])


@pytest.mark.integration
def test_solar_is_scaled(scenario, base_solar):
    tp = TransformProfile(
        scenario.ssh, scenario.info, scenario.state.get_grid(), scenario.state.get_ct()
    )
    scaled_solar = tp.get_solar()
    assert not base_solar.equals(scaled_solar)

    ct = scenario.state.get_ct()
    grid = scenario.state.get_grid()
    if "solar" in ct.keys():
        is_renewable_profile_scaled("solar", grid, ct, base_solar, scaled_solar)


@pytest.mark.integration
def test_wind_is_scaled(scenario, base_wind):
    grid = scenario.state.get_grid()
    ct = scenario.state.get_ct()

    # Scale a offshore wind turbine twice via zone_id and plant_id
    ct["wind_offshore"]["plant_id"][13905] = 0

    tp = TransformProfile(scenario.ssh, scenario.info, grid, ct)

    scaled_wind = tp.get_wind()
    assert not base_wind.equals(scaled_wind)

    if "wind" in ct.keys():
        is_renewable_profile_scaled("wind", grid, ct, base_wind, scaled_wind)


@pytest.mark.integration
def test_hydro_is_scaled(scenario, base_hydro):
    tp = TransformProfile(
        scenario.ssh, scenario.info, scenario.state.get_grid(), scenario.state.get_ct()
    )
    scaled_hydro = tp.get_hydro()
    assert not base_hydro.equals(scaled_hydro)

    ct = scenario.state.get_ct()
    grid = scenario.state.get_grid()
    if "hydro" in ct.keys():
        is_renewable_profile_scaled("hydro", grid, ct, base_hydro, scaled_hydro)


@pytest.mark.integration
def test_add_plant(scenario, base_solar, base_wind):
    new_plant = [
        {"type": "solar", "bus_id": 70040, "Pmax": 85},
        {"type": "wind", "bus_id": 9, "Pmin": 5, "Pmax": 60},
        {"type": "wind_offshore", "bus_id": 13802, "Pmax": 175},
        {"type": "wind_offshore", "bus_id": 13802, "Pmax": 100},
        {
            "type": "ng",
            "bus_id": 60374,
            "Pmin": 25,
            "Pmax": 400,
            "c0": 1500,
            "c1": 50,
            "c2": 0.5,
        },
    ]

    grid = scenario.state.get_grid()
    ct = ChangeTable(grid)

    ct.add_plant(new_plant)
    tg = TransformGrid(grid, ct.ct)
    new_grid = tg.get_grid()

    tp = TransformProfile(scenario.ssh, scenario.info, new_grid, ct.ct)

    new_solar = tp.get_solar()
    assert not new_solar.equals(base_solar)
    assert base_solar.equals(new_solar.drop(new_grid.plant.index[-5], axis=1))
    assert not len(base_solar.columns) == len(new_solar.columns)
    assert len(set(new_solar.columns) - set(base_solar.columns)) == 1
    assert set(new_solar.columns) - set(base_solar.columns) == {
        new_grid.plant.index[-5]
    }

    new_wind = tp.get_wind()
    assert not new_wind.equals(base_wind)
    assert base_wind.equals(new_wind.drop(new_grid.plant.index[-4:-1], axis=1))
    assert not len(base_wind.columns) == len(new_wind.columns)
    assert len(set(new_wind.columns) - set(base_wind.columns)) == 3
    assert set(new_wind.columns) - set(base_wind.columns) == set(
        new_grid.plant.index[-4:-1]
    )
