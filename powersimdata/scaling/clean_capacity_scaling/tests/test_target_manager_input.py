from powersimdata.scaling.clean_capacity_scaling.auto_capacity_scaling \
    import CollaborativeStrategyManager, IndependentStrategyManager, AbstractStrategyManager, TargetManager, Resource
import pandas as pd
import pytest


def test_can_pass():
    assert 1 == 1


def test_create_targets_from_dataframe():
    planning_data = {'strategy': ['Independent', 'Independent'], 'region_name': ['Pacific', 'Atlantic'],
                     'ce_category': ['Renewables', 'Clean'], 'ce_target_fraction': [.25, .4],
                     'total_demand': [200000, 300000], 'external_ce_historical_amount': [0, 0],
                     'solar_percentage':[.3,.6]}

    # future_data = {'total_demand': [200000, 300000], 'external_ce_total_gen': [ 0, 0]}

    planning_dataframe = pd.DataFrame.from_dict(planning_data)

    targets = {}
    for row in planning_dataframe.itertuples():
        targets[row.region_name] = TargetManager(row.region_name,
                                                 row.ce_target_fraction,
                                                 row.ce_category,
                                                 row.total_demand,
                                                 row.external_ce_historical_amount,
                                                 row.solar_percentage)

    assert targets['Pacific'].ce_category == planning_data['ce_category'][0]


def test_populate_strategy_from_dataframe():
    planning_data = {'strategy': ['Independent', 'Independent'], 'region_name': ['Pacific', 'Atlantic'],
                     'ce_category': ['Renewables', 'Clean'], 'ce_target_fraction': [.25, .4],
                     'total_demand': [200000, 300000], 'external_ce_historical_amount': [0, 0],
                     'solar_percentage':[.3,.6]}
    planning_dataframe = pd.DataFrame.from_dict(planning_data)

    strategy = AbstractStrategyManager()
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


def test_load_independent_test_case():
    pass


def test_load_collaborative_test_case():
    pass


def test_load_independent_western_case():
    western = pd.read_excel('Capacity_Scaling_Western_Test_Case.xlsx')

    resources_dict = {
        'coal': {'prev_generation': 'coal_generation', 'prev_capacity': 'coal_capacity'},
        'geothermal': {'prev_generation': 'geothermal_generation', 'prev_capacity': 'geothermal_capacity'},
        'ng': {'prev_generation': 'ng_generation', 'prev_capacity': 'ng_capacity'},
        'nuclear': {'prev_generation': 'nuclear_generation', 'prev_capacity': 'nuclear_capacity'},
        'hydro': {'prev_generation': 'hydro_generation', 'prev_capacity': 'hydro_capacity'},
        'solar': {'prev_generation': 'solar_generation', 'prev_capacity': 'solar_capacity',
                  'no_congestion_cap_factor': 'no_cong_solar_cf', 'prev_cap_factor': 'prev_sim_solar_cf'},
        'wind': {'prev_generation': 'wind_generation', 'prev_capacity': 'wind_capacity',
                 'no_congestion_cap_factor': 'no_cong_wind_cf', 'prev_cap_factor': 'prev_sim_wind_cf'}
    }

    strategy_manager = IndependentStrategyManager()
    for row in western.itertuples():
        target = TargetManager(row.State,
                               row.target_2030,
                               'CE category',
                               row.demand_2030,
                               row.external_count,
                               row.solar_percentage)

        allowed_resources = []
        if row.geothermal_counts == 'yes':
            allowed_resources.append('geothermal')
        if row.hydro_counts == 'yes':
            allowed_resources.append('hydro')
        if row.nuclear_counts == 'yes':
            allowed_resources.append('nuclear')
        if row.solar_counts == 'yes':
            allowed_resources.append('solar')
        if row.wind_counts == 'yes':
            allowed_resources.append('wind')
        target.set_allowed_resources(allowed_resources)

        for res, mapping in resources_dict.items():
            resource = Resource(res, 1)

            if res == 'solar' or res == 'wind':
                resource.set_capacity(
                    getattr(row, mapping['no_congestion_cap_factor']),
                    getattr(row, mapping['prev_capacity']),
                    getattr(row, mapping['prev_cap_factor'])
                )
            else:
                resource.set_capacity(
                    None,
                    getattr(row, mapping['prev_capacity']),
                    None
                )

            resource.set_generation(getattr(row, mapping['prev_generation']))
            target.add_resource(resource)

        strategy_manager.add_target(target)

    results = strategy_manager.data_frame_of_next_capacities()
    print(results)
    print(western[['State', 'solar_added_capacity_independent', 'wind_added_capacity_independent']])
    assert results.values.tolist() == western[['State', 'solar_added_capacity_independent', 'wind_added_capacity_independent']].values.tolist()

def test_load_collaborative_western_case():
    western = pd.read_excel('Capacity_Scaling_Western_Test_Case.xlsx')

    resources_dict = {
        'coal': {'prev_generation': 'coal_generation', 'prev_capacity': 'coal_capacity'},
        'geothermal': {'prev_generation': 'geothermal_generation', 'prev_capacity': 'geothermal_capacity'},
        'ng': {'prev_generation': 'ng_generation', 'prev_capacity': 'ng_capacity'},
        'nuclear': {'prev_generation': 'nuclear_generation', 'prev_capacity': 'nuclear_capacity'},
        'hydro': {'prev_generation': 'hydro_generation', 'prev_capacity': 'hydro_capacity'},
        'solar': {'prev_generation': 'solar_generation', 'prev_capacity': 'solar_capacity',
                  'no_congestion_cap_factor': 'no_cong_solar_cf', 'prev_cap_factor': 'prev_sim_solar_cf'},
        'wind': {'prev_generation': 'wind_generation', 'prev_capacity': 'wind_capacity',
                 'no_congestion_cap_factor': 'no_cong_wind_cf', 'prev_cap_factor': 'prev_sim_wind_cf'}
    }

    strategy_manager = CollaborativeStrategyManager()
    for row in western.itertuples():
        target = TargetManager(row.State,
                               row.target_2030,
                               'CE category',
                               row.demand_2030,
                               row.external_count,
                               row.solar_percentage)

        allowed_resources = []
        if row.geothermal_counts == 'yes':
            allowed_resources.append('geothermal')
        if row.hydro_counts == 'yes':
            allowed_resources.append('hydro')
        if row.nuclear_counts == 'yes':
            allowed_resources.append('nuclear')
        if row.solar_counts == 'yes':
            allowed_resources.append('solar')
        if row.wind_counts == 'yes':
            allowed_resources.append('wind')
        target.set_allowed_resources(allowed_resources)

        for res, mapping in resources_dict.items():
            resource = Resource(res, 1)

            if res == 'solar' or res == 'wind':
                resource.set_capacity(
                    getattr(row, mapping['no_congestion_cap_factor']),
                    getattr(row, mapping['prev_capacity']),
                    getattr(row, mapping['prev_cap_factor'])
                )
            else:
                resource.set_capacity(
                    None,
                    getattr(row, mapping['prev_capacity']),
                    None
                )

            resource.set_generation(getattr(row, mapping['prev_generation']))
            target.add_resource(resource)

        strategy_manager.add_target(target)

    results = strategy_manager.data_frame_of_next_capacities()
    print(results)
    print(western[['State', 'solar_added_capacity_collaborative', 'wind_added_capacity_collaborative']])
    assert results.values.tolist() == western[['State', 'solar_added_capacity_collaborative', 'wind_added_capacity_collaborative']].values.tolist()
