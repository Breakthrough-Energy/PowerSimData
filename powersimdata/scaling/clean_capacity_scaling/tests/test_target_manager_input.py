from powersimdata.scaling.clean_capacity_scaling.auto_capacity_scaling import TargetManager, AbstractStrategy, Resource
import pandas as pd
import pytest


def test_can_pass():
    assert 1 == 1


def test_create_targets_from_dataframe():
    planning_data = {'strategy': ['Independent', 'Independent'], 'region_name': ['Pacific', 'Atlantic'],
                     'ce_category': ['Renewables', 'Clean'], 'ce_target_fraction': [.25, .4],
                     'total_demand': [200000, 300000], 'external_ce_total_gen': [ 0, 0]}

    # future_data = {'total_demand': [200000, 300000], 'external_ce_total_gen': [ 0, 0]}

    planning_dataframe = pd.DataFrame.from_dict(planning_data)

    targets = {}
    for row in planning_dataframe.itertuples():
        targets[row.region_name] = TargetManager(row.region_name, row.ce_target_fraction, row.ce_category, row.total_demand)

    assert targets['Pacific'].ce_category == planning_data['ce_category'][0]


def test_populate_strategy_from_dataframe():
    planning_data = {'strategy': ['Independent', 'Independent'], 'region_name': ['Pacific', 'Atlantic'],
                     'ce_category': ['Renewables', 'Clean'], 'ce_target_fraction': [.25, .4],
                     'total_demand': [200000, 300000], 'external_ce_total_gen': [ 0, 0]}
    planning_dataframe = pd.DataFrame.from_dict(planning_data)

    strategy = AbstractStrategy()
    strategy.targets_from_data_frame(planning_dataframe)

    assert strategy.targets['Pacific'].ce_category == planning_data['ce_category'][0]


@pytest.mark.skip(reason="doesn't work yet")
def test_create_resources_from_dataframe():
    pacific_resource_data = {'resource_name': ['geo', 'hydro', 'nuclear', 'solar', 'wind'],
                     'generation': [8000.0, 7000.0, 6000.0, 8125.0, 12648.96],
                     'capacity': [4000.0, 3900.0, 3800.0, 3700.0, 3600.0]}
    pacific_resource_dataframe = pd.DataFrame.from_dict(pacific_resource_data)

    atlantic_resource_data = {'resource_name': ['geo', 'hydro', 'nuclear', 'solar', 'wind'],
                     'generation': [8500.0, 7500.0, 6500.0, 11067.84, 12605.04],
                     'capacity': [4500.0, 4400.0, 4300.0, 4200.0, 4100.0]}
    atlantic_resource_dataframe = pd.DataFrame.from_dict(atlantic_resource_data)


    planning_data = {'strategy': ['Independent', 'Independent'], 'region_name': ['Pacific', 'Atlantic'],
                     'ce_category': ['Renewables', 'Clean'], 'ce_target_fraction': [.25, .4],
                     'total_demand': [200000, 300000], 'external_ce_total_gen': [0, 0],
                     'resources': [pacific_resource_dataframe, atlantic_resource_dataframe]}

    # future_data = {'total_demand': [200000, 300000], 'external_ce_total_gen': [ 0, 0]}

    targets = {}
    for target_manager_obj in planning_dataframe.itertuples():
        target_manager_obj = TargetManager(target_manager_obj.region_name, target_manager_obj.ce_target_fraction,
                                          target_manager_obj.ce_category, target_manager_obj.total_demand)
        for resource in target_manager_obj.resources.itertuples():
            res_obj = Resource(resource.name, 1)
            res_obj.set_capacity(resource.capacity, resource.capacity, resource.capacity)
            res_obj.set_generation(resource.generation)
            target_manager_obj.add_resource(resource)
        targets[target_manager_obj.region_name] = target_manager_obj
