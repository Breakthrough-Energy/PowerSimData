import pytest

from powersimdata.input.profiles import InputData
from powersimdata.utility.transfer_data import setup_server_connection
from powersimdata.input.change_table import ChangeTable
from powersimdata.scenario.scenario import Scenario
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile

ssh_client = setup_server_connection()
input_data = InputData(ssh_client)
scenario_id = '564'


@pytest.fixture(scope="module")
def scenario():
    return Scenario(scenario_id)


@pytest.fixture(scope="module")
def base_hydro():
    return input_data.get_data(scenario_id, 'hydro')


@pytest.fixture(scope="module")
def base_wind():
    return input_data.get_data(scenario_id, 'wind')


@pytest.fixture(scope="module")
def base_solar():
    return input_data.get_data(scenario_id, 'solar')


@pytest.fixture(scope="module")
def base_demand():
    return input_data.get_data(scenario_id, 'demand')


@pytest.mark.integration
def test_demand_is_scaled(scenario, base_demand):
    tp = TransformProfile(ssh_client, scenario_id,
                          scenario.state.get_grid(),
                          scenario.state.get_ct())
    scaled_demand = tp.get_demand()
    assert not base_demand.equals(scaled_demand)

    ct = scenario.state.get_ct()
    grid = scenario.state.get_grid()
    if 'demand' in ct.keys():
        scaled_zone = list(ct['demand']['zone_id'].keys())
        unscaled_zone = set(grid.id2zone.keys()) - set(scaled_zone)
        factor = list(ct['demand']['zone_id'].values())
        assert scaled_demand[scaled_zone].equals(
            base_demand[scaled_zone].multiply(factor, axis=1))
        if unscaled_zone:
            assert scaled_demand[unscaled_zone].equals(
                base_demand[unscaled_zone])


@pytest.mark.integration
def test_solar_is_scaled(scenario, base_solar):
    tp = TransformProfile(ssh_client, scenario_id,
                          scenario.state.get_grid(),
                          scenario.state.get_ct())
    scaled_solar = tp.get_solar()
    assert not base_solar.equals(scaled_solar)

    ct = scenario.state.get_ct()
    grid = scenario.state.get_grid()
    if 'solar' in ct.keys():
        scaled_plant_id = []
        scaling_factor_plant = []
        if 'zone_id' in ct['solar'].keys():
            scaled_zone = list(ct['solar']['zone_id'].keys())
            scaling_factor_for_zone = list(ct['solar']['zone_id'].values())
            for z, f in zip(scaled_zone, scaling_factor_for_zone):
                plant_id_zone = grid.plant.groupby(
                    ['zone_id', 'type']).get_group((z, 'solar')).index.tolist()
                scaled_plant_id += plant_id_zone
                scaling_factor_plant += [f] * len(plant_id_zone)
        if 'plant_id' in ct['solar'].keys():
            for i, f in ct['solar']['plant_id'].items():
                if i in scaled_plant_id:
                    scaling_factor_plant[scaled_plant_id.index(i)] *= f
                else:
                    scaled_plant_id.append(i)
                    scaling_factor_plant.append(f)
        assert scaled_solar[scaled_plant_id].equals(
            base_solar[scaled_plant_id].multiply(scaling_factor_plant, axis=1))

        all_plant_id = grid.plant.groupby('type').get_group(
            'solar').index.tolist()
        unscaled_plant_id = set(all_plant_id) - set(scaled_plant_id)
        if unscaled_plant_id:
            assert scaled_solar[unscaled_plant_id].equals(
                base_solar[unscaled_plant_id])


@pytest.mark.integration
def test_wind_is_scaled(scenario, base_wind):
    grid = scenario.state.get_grid()
    ct = scenario.state.get_ct()

    # Scale a offshore wind turbine twice via zone_id and plant_id
    ct['wind_offshore']['plant_id'][13905] = 0

    tp = TransformProfile(ssh_client, scenario_id, grid, ct)

    scaled_wind = tp.get_wind()
    assert not base_wind.equals(scaled_wind)

    if 'wind' in ct.keys():
        scaled_plant_id = []
        scaling_factor_plant = []
        if 'zone_id' in ct['wind'].keys():
            scaled_zone = list(ct['wind']['zone_id'].keys())
            scaling_factor_for_zone = list(ct['wind']['zone_id'].values())
            for z, f in zip(scaled_zone, scaling_factor_for_zone):
                plant_id_zone = grid.plant.groupby(
                    ['zone_id', 'type']).get_group((z, 'wind')).index.tolist()
                scaled_plant_id += plant_id_zone
                scaling_factor_plant += [f] * len(plant_id_zone)
        if 'plant_id' in ct['wind'].keys():
            for i, f in ct['solar']['plant_id'].items():
                if i in scaled_plant_id:
                    scaling_factor_plant[scaled_plant_id.index(i)] *= f
                else:
                    scaled_plant_id.append(i)
                    scaling_factor_plant.append(f)
        assert scaled_wind[scaled_plant_id].equals(
            base_wind[scaled_plant_id].multiply(scaling_factor_plant, axis=1))

        all_plant_id = grid.plant.groupby('type').get_group(
            'wind').index.tolist()
        unscaled_plant_id = set(all_plant_id) - set(scaled_plant_id)
        if unscaled_plant_id:
            assert scaled_wind[unscaled_plant_id].equals(
                base_wind[unscaled_plant_id])


@pytest.mark.integration
def test_hydro_is_scaled(scenario, base_hydro):
    tp = TransformProfile(ssh_client, scenario_id,
                          scenario.state.get_grid(),
                          scenario.state.get_ct())
    scaled_hydro = tp.get_hydro()
    assert not base_hydro.equals(scaled_hydro)

    ct = scenario.state.get_ct()
    grid = scenario.state.get_grid()
    if 'hydro' in ct.keys():
        scaled_plant_id = []
        scaling_factor_plant = []
        if 'zone_id' in ct['hydro'].keys():
            scaled_zone = list(ct['hydro']['zone_id'].keys())
            scaling_factor_for_zone = list(ct['hydro']['zone_id'].values())
            for z, f in zip(scaled_zone, scaling_factor_for_zone):
                plant_id_zone = grid.plant.groupby(
                    ['zone_id', 'type']).get_group((z, 'hydro')).index.tolist()
                scaled_plant_id += plant_id_zone
                scaling_factor_plant += [f] * len(plant_id_zone)
        if 'plant_id' in ct['hydro'].keys():
            for i, f in ct['solar']['plant_id'].items():
                if i in scaled_plant_id:
                    scaling_factor_plant[scaled_plant_id.index(i)] *= f
                else:
                    scaled_plant_id.append(i)
                    scaling_factor_plant.append(f)
        assert scaled_hydro[scaled_plant_id].equals(
            base_hydro[scaled_plant_id].multiply(scaling_factor_plant, axis=1))

        all_plant_id = grid.plant.groupby('type').get_group(
            'hydro').index.tolist()
        unscaled_plant_id = set(all_plant_id) - set(scaled_plant_id)
        if unscaled_plant_id:
            assert scaled_hydro[unscaled_plant_id].equals(
                base_hydro[unscaled_plant_id])


@pytest.mark.integration
def test_add_plant(scenario, base_solar, base_wind):
    new_plant = [
        {'type': 'solar', 'bus_id': 70040, 'Pmax': 85},
        {'type': 'wind', 'bus_id': 9, 'Pmin': 5, 'Pmax': 60},
        {'type': 'wind_offshore', 'bus_id': 13802, 'Pmax': 175},
        {'type': 'ng', 'bus_id': 60374, 'Pmin': 25, 'Pmax': 400,
         'c0': 1500, 'c1': 50, 'c2': 0.5}]

    grid = scenario.state.get_grid()
    ct = ChangeTable(grid)

    ct.add_plant(new_plant)
    tg = TransformGrid(grid, ct.ct)
    new_grid = tg.get_grid()

    tp = TransformProfile(ssh_client, scenario_id, new_grid, ct.ct)

    new_solar = tp.get_solar()
    assert not new_solar.equals(base_solar)
    assert base_solar.equals(new_solar.drop(new_grid.plant.index[-4], axis=1))
    assert not len(base_solar.columns) == len(new_solar.columns)
    assert len(set(new_solar.columns) - set(base_solar.columns)) == 1
    assert set(new_solar.columns) - set(base_solar.columns) == {
        new_grid.plant.index[-4]}

    new_wind = tp.get_wind()
    assert not new_wind.equals(base_wind)
    assert base_wind.equals(new_wind.drop(new_grid.plant.index[-3:-1], axis=1))
    assert not len(base_wind.columns) == len(new_wind.columns)
    assert len(set(new_wind.columns) - set(base_wind.columns)) == 2
    assert set(new_wind.columns) - set(base_wind.columns) == set(
        new_grid.plant.index[-3:-1])
