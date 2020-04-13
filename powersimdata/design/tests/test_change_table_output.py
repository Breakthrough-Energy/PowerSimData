import pandas as pd
from pytest import approx, raises
from powersimdata.input.grid import Grid
from powersimdata.design.clean_capacity_scaling\
    import IndependentStrategyManager, Resource

from powersimdata.design.clean_capacity_scaling\
    import TargetManager, ResourceManager, CollaborativeStrategyManager

from powersimdata.design.tests.test_strategies\
    import _build_collaborative_test_atlantic_resources, \
    _build_collaborative_test_pacific_resources


def test_change_table_output():
    collab = _setup_collaborative_strategy()

    mock_plant = {
            'plant_id': [101, 102, 103, 104, 105, 106],
            'bus_id': [1001, 1002, 1003, 1004, 1005, 1006],
            'type': ['solar', 'wind', 'geo', 'solar', 'nuclear', 'hydro'],
            'zone_name': ['Pacific', 'Atlantic', 'Atlantic', 'Pacific',
                          'Pacific', 'Pacific'],
            'GenFuelCost': [0, 0, 3.3, 4.4, 5.5, 0],
            'Pmin': [0, 0, 0, 0, 0, 0],
            'Pmax': [50, 200, 80, 100, 120, 220],
            }

    scale_factor_table = collab.create_scale_factor_table(GridMock(mock_plant))

    answer = {'solar': {'Pacific': 62.00925925925926},
              'nuclear': {'Pacific': 35.833333333333336},
              'hydro': {'Pacific': 17.727272727272727},
              'wind': {'Atlantic': 45.24999999999999},
              'geo': {'Atlantic': 50.0}}
    assert len(scale_factor_table) == len(answer)
    for gen_type, next_level in scale_factor_table.items():
        assert len(next_level) == len(answer[gen_type])
        for region_name, scale_factor in next_level.items():
            assert scale_factor == approx(answer[gen_type][region_name])

    next_capacities = collab.data_frame_of_next_capacities()[[
        'next_solar_capacity', 'next_wind_capacity']]
    assert scale_factor_table['solar']['Pacific'] == \
        next_capacities.loc['Pacific', 'next_solar_capacity']/150
    assert scale_factor_table['wind']['Atlantic'] == \
        next_capacities.loc['Atlantic', 'next_wind_capacity']/200

    assert scale_factor_table['geo']['Atlantic'] == collab.targets[
        'Atlantic'].resources['geo'].prev_capacity / 80
    assert scale_factor_table['nuclear']['Pacific'] == collab.targets[
        'Pacific'].resources['nuclear'].prev_capacity / 120
    assert scale_factor_table['hydro']['Pacific'] == collab.targets[
        'Pacific'].resources['hydro'].prev_capacity / 220


class GridMock:
    def __init__(self, mock_plant):
        self.zone2id = {'Pacific': 1, 'Atlantic': 2}
        self.plant = pd.DataFrame(mock_plant)
        self.plant.set_index('plant_id', inplace=True)


def _setup_collaborative_strategy():
    # create Pacific
    pacific_target = TargetManager('Pacific', 0, 'renewables', 200000*1000)
    pacific_target.set_allowed_resources(['solar', 'wind', 'geo'])
    pacific_resources = _build_collaborative_test_pacific_resources()
    resources_dict = {}
    for r in pacific_resources:
        resources_dict[r.name] = r
    pacific_resources = ResourceManager()
    pacific_resources.resources = resources_dict
    pacific_target.add_resource_manager(pacific_resources)

    # create Atlantic
    atlantic_target = TargetManager('Atlantic', 0.4, 'clean', 300000*1000)
    atlantic_target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro',
                                           'nuclear'])
    atlantic_resources = _build_collaborative_test_atlantic_resources()
    resources_dict = {}
    for r in atlantic_resources:
        resources_dict[r.name] = r
    atlantic_resources = ResourceManager()
    atlantic_resources.resources = resources_dict
    atlantic_target.add_resource_manager(pacific_resources)

    collab = CollaborativeStrategyManager()
    collab.set_next_sim_hours(8784)
    collab.add_target(pacific_target)
    collab.add_target(atlantic_target)
    return collab


def test_change_table_output_from_capacities_dataframe():
    gen_capacity = _create_capacities_dataframe()
    strategy = IndependentStrategyManager()
    scale_factor_table = strategy.create_scale_factor_table(
        Grid(['Eastern']), gen_capacity)
    print(scale_factor_table)

    answer = {'solar':
                  {'Maine': 4.0},
              'wind':
                  {'Western North Carolina': 3.0,
                   'North Carolina': 3.0,
                   'Florida North': 20.0,
                   'Florida Panhandle': 20.0,
                   'Florida South': 20.0}}

    assert len(scale_factor_table) == len(answer)
    for gen_type, next_level in scale_factor_table.items():
        assert len(next_level) == len(answer[gen_type])
        for region_name, scale_factor in next_level.items():
            assert scale_factor == approx(answer[gen_type][region_name])


def _create_capacities_dataframe():
    data = {'coal': {'Maine': 0.0,
                     'North Carolina': 11494.205,
                     'Florida': 11090.296},
            'dfo': {'Maine': 917.597,
                    'North Carolina': 490.80100000000004,
                    'Florida': 5663.306},
            'hydro': {'Maine': 714.8,
                      'North Carolina': 1985.3899999999999,
                      'Florida': 55.701},
            'ng': {'Maine': 1758.198,
                   'North Carolina': 13154.294,
                   'Florida': 47986.782999999996},
            'other': {'Maine': 361.0,
                      'North Carolina': 365.754,
                      'Florida': 886.998},
            'solar': {'Maine': 1.0 * 4,
                      'North Carolina': 3550.216,
                      'Florida': 1862.899},
            'wind': {'Maine': 898.8,
                     'North Carolina': 209.0 * 3,
                     'Florida': 3.0 * 20},
            'nuclear': {'Maine': 0.0,
                        'North Carolina': 4875.788,
                        'Florida': 3341.23}}
    return pd.DataFrame(data)


def test_state_split_two_interconnects():
    gen_capacity = _create_texas_solar_dataframe()
    strategy = IndependentStrategyManager()
    scale_factor_table = strategy.create_scale_factor_table(
        Grid(['Eastern']), gen_capacity)
    print(scale_factor_table)

    answer = {'solar': {'Texas Panhandle': 10, 'East Texas': 10}}

    assert len(scale_factor_table) == len(answer)
    for gen_type, next_level in scale_factor_table.items():
        assert len(next_level) == len(answer[gen_type])
        for region_name, scale_factor in next_level.items():
            assert scale_factor == approx(answer[gen_type][region_name])


def _create_texas_solar_dataframe():
    data = {'solar': {'Texas': 20}}
    return pd.DataFrame(data)