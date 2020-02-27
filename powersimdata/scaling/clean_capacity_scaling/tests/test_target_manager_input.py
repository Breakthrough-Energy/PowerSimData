from powersimdata.scaling.clean_capacity_scaling.auto_capacity_scaling \
    import CollaborativeStrategyManager, IndependentStrategyManager, AbstractStrategyManager, TargetManager, Resource
import pandas as pd
import pytest


def test_create_targets_from_dataframe():
    planning_data = {'strategy': ['Independent', 'Independent'],
                     'region_name': ['Pacific', 'Atlantic'],
                     'ce_category': ['Renewables', 'Clean'],
                     'ce_target_fraction': [.25, .4],
                     'total_demand': [200000, 300000],
                     'external_ce_historical_amount': [0, 0],
                     'solar_percentage': [.3, .6]}

    # future_data = {'total_demand': [200000, 300000],
    # 'external_ce_total_gen': [ 0, 0]}

    planning_dataframe = pd.DataFrame.from_dict(planning_data)

    targets = {}
    for row in planning_dataframe.itertuples():
        targets[row.region_name] = TargetManager(
            row.region_name,
            row.ce_target_fraction,
            row.ce_category,
            row.total_demand,
            row.external_ce_historical_amount,
            row.solar_percentage)

    assert targets['Pacific'].ce_category == planning_data['ce_category'][0]


def test_populate_strategy_from_dataframe():
    planning_data = {'strategy': ['Independent', 'Independent'],
                     'region_name': ['Pacific', 'Atlantic'],
                     'ce_category': ['Renewables', 'Clean'],
                     'ce_target_fraction': [.25, .4],
                     'total_demand': [200000, 300000],
                     'external_ce_historical_amount': [0, 0],
                     'solar_percentage': [.3, .6]}
    planning_dataframe = pd.DataFrame.from_dict(planning_data)

    strategy = AbstractStrategyManager()
    strategy.targets_from_data_frame(planning_dataframe)

    assert strategy.targets['Pacific'].ce_category == \
        planning_data['ce_category'][0]
