from powersimdata.scaling.clean_capacity_scaling.auto_capacity_scaling\
    import Resource, TargetManager, AbstractStrategyManager, \
    IndependentStrategyManager, CollaborativeStrategyManager
from pytest import approx, raises


def test_independent_capacity_strategy():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.25)
    solar.set_generation(8125.2*1000)
    solar.set_curtailment(0)
    solar.set_addl_curtailment(0.40)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.4)
    wind.set_generation(12648.96*1000)
    wind.set_curtailment(0)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)

    AbstractStrategyManager.set_next_sim_hours(8784)
    solar_added, wind_added = target.calculate_added_capacity()
    assert wind_added == approx(4360.459)
    assert solar_added == approx(4481.582)


def test_independent_capacity_strategy_Atlantic_2():
    solar = Resource('solar', 3)
    solar.set_capacity(0.3, 4200, 0.3)
    solar.set_generation(11067.84*1000)
    solar.set_curtailment(0)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.35, 4100, 0.35)
    wind.set_generation(12605.04*1000)
    wind.set_curtailment(0)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4500, 1)
    geo.set_generation(8500*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 4400, 1)
    hydro.set_generation(7500*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 4300, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Atlantic', 0.3, 'renewables', 300000*1000)
    target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(39672.88*1000)
    ce_shortfall = target.calculate_ce_shortfall()
    assert ce_shortfall == approx(50327.12*1000)

    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(8928.948)
    assert wind_added == approx(8716.354)


def test_independent_capacity_strategy_pacific_3():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000*1000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000*1000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6000*1000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(26000*1000)
    ce_shortfall = target.calculate_ce_shortfall()
    assert ce_shortfall == approx(24000*1000)

    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(4933.333)
    assert wind_added == approx(4800)


def test_independent_capacity_strategy_atlantic_4():
    solar = Resource('solar', 3)
    solar.set_capacity(0.3, 4200, 0.284608)
    solar.set_generation(10500*1000)
    solar.set_curtailment(0.051305)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.35, 4100, 0.319317)
    wind.set_generation(11500*1000)
    wind.set_curtailment(0.087667)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4500, 1)
    geo.set_generation(8500*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 4400, 1)
    hydro.set_generation(7500*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 4300, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Atlantic', 0.4, 'clean', 300000*1000)
    target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro', 'nuclear'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(44500*1000)
    ce_shortfall = target.calculate_ce_shortfall()
    assert ce_shortfall == approx(75500*1000)

    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(14413.636)
    assert wind_added == approx(14070.455)


def test_independent_capacity_strategy_pacific_external_6():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000*1000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000*1000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000,
                           40000*1000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = target.calculate_prev_ce_generation()
    assert prev_ce_generation == 26000*1000
    ce_shortfall = target.calculate_ce_shortfall()
    assert ce_shortfall == approx(10000*1000)
    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(2055.556)
    assert wind_added == approx(2000)


def test_independent_capacity_strategy_pacific_solar0_7():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000*1000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000*1000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000, 0, 0)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = target.calculate_prev_ce_generation()
    assert prev_ce_generation == 26000*1000
    ce_shortfall = target.calculate_ce_shortfall()
    assert ce_shortfall == approx(24000*1000)
    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(0)
    assert wind_added == approx(7854.545)


def test_independent_capacity_strategy_pacific_solar75_8():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000*1000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000*1000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000,
                           0, 0.75)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = target.calculate_prev_ce_generation()
    assert prev_ce_generation == 26000*1000
    ce_shortfall = target.calculate_ce_shortfall()
    assert ce_shortfall == approx(24000*1000)
    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(8246.26)
    assert wind_added == approx(2748.753)


def test_independent_capacity_strategy_pacific_solar100_9():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379314)
    solar.set_generation(7000*1000)
    solar.set_curtailment(0.138482745)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347854685)
    wind.set_generation(11000*1000)
    wind.set_curtailment(0.130363287)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000, 0, 1)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = target.calculate_prev_ce_generation()
    assert prev_ce_generation == 26000*1000
    ce_shortfall = target.calculate_ce_shortfall()
    assert ce_shortfall == approx(24000*1000)
    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(12685.714)
    assert wind_added == 0


def test_independent_capacity_strategy_windcurtail_10():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000*1000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000*1000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0.15)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000*1000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000*1000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000, 0, 0.75)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    AbstractStrategyManager.set_next_sim_hours(8784)
    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(8703.117)
    assert wind_added == approx(2901.039)


def _build_collaborative_test_pacific_resources():
    # Common resources to be used for Pacific target in test_collaborative_*()
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000*1000)
    solar.set_curtailment(0.138483)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000*1000)
    wind.set_curtailment(0.130363)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000*1000)
    geo.set_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000*1000)
    hydro.set_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 4300, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)

    return [solar, wind, geo, hydro, nuclear]


def _build_collaborative_test_atlantic_resources():
    # Common resources to be used for Atlantic target in test_collaborative_*()
    solar = Resource('solar', 3)
    solar.set_capacity(0.3, 4200, 0.284608)
    solar.set_generation(10500*1000)
    solar.set_curtailment(0.051305)

    wind = Resource('wind', 3)
    wind.set_capacity(0.35, 4100, 0.319317)
    wind.set_generation(11500*1000)
    wind.set_curtailment(0.087667)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4500, 1)
    geo.set_generation(8500*1000)
    geo.set_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 4400, 1)
    hydro.set_generation(7500*1000)
    hydro.set_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 4300, 1)
    nuclear.set_generation(6500*1000)
    nuclear.set_curtailment(0)

    return [solar, wind, geo, hydro, nuclear]


def test_collaborative_capacity_strategy():
    # create Pacific
    pacific_target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000)
    pacific_target.set_allowed_resources(['solar', 'wind', 'geo'])
    pacific_resources = _build_collaborative_test_pacific_resources()
    for r in pacific_resources:
        pacific_target.add_resource(r)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = pacific_target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(26000*1000)
    ce_shortfall = pacific_target.calculate_ce_shortfall()
    assert ce_shortfall == approx(24000*1000)

    # create Atlantic
    atlantic_target = TargetManager('Atlantic', 0.4, 'clean', 300000*1000)
    atlantic_target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro',
                                           'nuclear'])
    atlantic_resources = _build_collaborative_test_atlantic_resources()
    for r in atlantic_resources:
        atlantic_target.add_resource(r)

    prev_ce_generation = atlantic_target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(44500*1000)
    ce_shortfall = atlantic_target.calculate_ce_shortfall()
    assert ce_shortfall == approx(75500*1000)

    collab = CollaborativeStrategyManager()
    collab.add_target(pacific_target)
    collab.add_target(atlantic_target)

    collab_ce_shortfall = collab.calculate_total_shortfall()
    assert collab_ce_shortfall == approx(99500*1000)
    collab_prev_ce_generation = collab.calculate_total_prev_ce_generation()
    assert collab_prev_ce_generation == approx(70500*1000)

    solar_added, wind_added = collab.calculate_total_added_capacity()
    assert solar_added == approx(19651.25)
    assert wind_added == approx(19153.75)

    solar_scaling, wind_scaling = collab.calculate_capacity_scaling()
    assert collab.targets['Pacific'].resources['solar'].prev_capacity *\
        solar_scaling == approx(3700 + 9203.75)
    assert collab.targets['Pacific'].resources['wind'].prev_capacity *\
        wind_scaling == approx(3600 + 8955)
    assert collab.targets['Atlantic'].resources['solar'].prev_capacity *\
        solar_scaling == approx(4200 + 10447.5)
    assert collab.targets['Atlantic'].resources['wind'].prev_capacity *\
        wind_scaling == approx(4100 + 10198.75)


def test_collaborative_capacity_strategy_overgeneration():
    # create Pacific
    pacific_target = TargetManager('Pacific', 0, 'renewables', 200000*1000)
    pacific_target.set_allowed_resources(['solar', 'wind', 'geo'])
    pacific_resources = _build_collaborative_test_pacific_resources()
    for r in pacific_resources:
        pacific_target.add_resource(r)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = pacific_target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(26000*1000)
    ce_shortfall = pacific_target.calculate_ce_shortfall()
    assert ce_shortfall == 0

    # create Atlantic
    atlantic_target = TargetManager('Atlantic', 0.4, 'clean', 300000*1000)
    atlantic_target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro',
                                           'nuclear'])
    atlantic_resources = _build_collaborative_test_atlantic_resources()
    for r in atlantic_resources:
        atlantic_target.add_resource(r)

    prev_ce_generation = atlantic_target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(44500*1000)
    ce_shortfall = atlantic_target.calculate_ce_shortfall()
    assert ce_shortfall == approx(75500*1000)

    collab = CollaborativeStrategyManager()
    collab.add_target(pacific_target)
    collab.add_target(atlantic_target)

    collab_ce_shortfall = collab.calculate_total_shortfall()
    assert collab_ce_shortfall == approx(49500*1000)
    collab_prev_ce_generation = collab.calculate_total_prev_ce_generation()
    assert collab_prev_ce_generation == approx(70500*1000)

    solar_added, wind_added = collab.calculate_total_added_capacity()
    assert solar_added == approx(9776.25)
    assert wind_added == approx(9528.75)

    solar_scaling, wind_scaling = collab.calculate_capacity_scaling()
    assert collab.targets['Pacific'].resources['solar'].prev_capacity *\
        solar_scaling == approx(3700 + 4578.75)
    assert collab.targets['Pacific'].resources['wind'].prev_capacity *\
        wind_scaling == approx(3600 + 4455)
    assert collab.targets['Atlantic'].resources['solar'].prev_capacity *\
        solar_scaling == approx(4200 + 5197.5)
    assert collab.targets['Atlantic'].resources['wind'].prev_capacity *\
        wind_scaling == approx(4100 + 5073.75)


def test_collaborative_capacity_strategy_collab_curtailment():
    # create Pacific
    pacific_target = TargetManager('Pacific', 0.25, 'renewables', 200000*1000)
    pacific_target.set_allowed_resources(['solar', 'wind', 'geo'])
    pacific_resources = _build_collaborative_test_pacific_resources()
    for r in pacific_resources:
        pacific_target.add_resource(r)

    AbstractStrategyManager.set_next_sim_hours(8784)
    prev_ce_generation = pacific_target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(26000*1000)
    ce_shortfall = pacific_target.calculate_ce_shortfall()
    assert ce_shortfall == approx(24000*1000)

    # create Atlantic
    atlantic_target = TargetManager('Atlantic', 0.4, 'clean', 300000*1000)
    atlantic_target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro',
                                           'nuclear'])
    atlantic_resources = _build_collaborative_test_atlantic_resources()
    for r in atlantic_resources:
        atlantic_target.add_resource(r)

    prev_ce_generation = atlantic_target.calculate_prev_ce_generation()
    assert prev_ce_generation == approx(44500*1000)
    ce_shortfall = atlantic_target.calculate_ce_shortfall()
    assert ce_shortfall == approx(75500*1000)

    collab = CollaborativeStrategyManager()
    collab.add_target(pacific_target)
    collab.add_target(atlantic_target)
    collab.set_collab_addl_curtailment({'solar':0.07, 'wind': 0.13})

    collab_ce_shortfall = collab.calculate_total_shortfall()
    assert collab_ce_shortfall == approx(99500*1000)
    collab_prev_ce_generation = collab.calculate_total_prev_ce_generation()
    assert collab_prev_ce_generation == approx(70500*1000)

    solar_added, wind_added = collab.calculate_total_added_capacity()
    assert solar_added == approx(21926.08)
    assert wind_added == approx(21370.99)

    solar_scaling, wind_scaling = collab.calculate_capacity_scaling()
    assert collab.targets['Pacific'].resources['solar'].prev_capacity *\
        solar_scaling == approx(3700 + 10269.18)
    assert collab.targets['Pacific'].resources['wind'].prev_capacity *\
        wind_scaling == approx(3600 + 9991.63)
    assert collab.targets['Atlantic'].resources['solar'].prev_capacity *\
        solar_scaling == approx(4200 + 11656.9)
    assert collab.targets['Atlantic'].resources['wind'].prev_capacity *\
        wind_scaling == approx(4100 + 11379.36)


def test_adding_addl_curtailment():
    # create Pacific
    pacific_solar = Resource('solar', 3)
    pacific_solar.set_capacity(0.25, 3700, 0.215379)
    pacific_solar.set_generation(7000 * 1000)
    pacific_solar.set_curtailment(0.138483)
    pacific_solar.set_addl_curtailment(0)

    pacific_wind = Resource('wind', 3)
    pacific_wind.set_capacity(0.4, 3600, 0.347855)
    pacific_wind.set_generation(11000 * 1000)
    pacific_wind.set_curtailment(0.130363)
    pacific_wind.set_addl_curtailment(0)

    pacific_target = TargetManager('Pacific', 0.25, 'renewables',
                                   200000 * 1000)
    pacific_target.set_allowed_resources(['solar', 'wind', 'geo'])

    pacific_target.add_resource(pacific_solar)
    pacific_target.add_resource(pacific_wind)

    # create Atlantic
    atlantic_solar = Resource('solar', 3)
    atlantic_solar.set_capacity(0.3, 4200, 0.284608)
    atlantic_solar.set_generation(10500 * 1000)
    atlantic_solar.set_curtailment(0.051305)
    atlantic_solar.set_addl_curtailment(0)

    atlantic_wind = Resource('wind', 3)
    atlantic_wind.set_capacity(0.35, 4100, 0.319317)
    atlantic_wind.set_generation(11500 * 1000)
    atlantic_wind.set_curtailment(0.087667)
    atlantic_wind.set_addl_curtailment(0)

    atlantic_target = TargetManager('Atlantic', 0.4, 'clean', 300000 * 1000)
    atlantic_target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro',
                                           'nuclear'])
    atlantic_target.add_resource(atlantic_solar)
    atlantic_target.add_resource(atlantic_wind)

    independent_strategy_manager = IndependentStrategyManager()
    independent_strategy_manager.add_target(pacific_target)
    independent_strategy_manager.add_target(atlantic_target)

    independent_strategy_manager.set_addl_curtailment({"Pacific": {
        "solar": .2, "wind": .5}})

    assert independent_strategy_manager.targets["Pacific"].resources[
        'solar'].addl_curtailment == .2
    assert independent_strategy_manager.targets["Pacific"].resources[
        'wind'].addl_curtailment == .5
    assert independent_strategy_manager.targets["Atlantic"].resources[
        'solar'].addl_curtailment == 0
    assert independent_strategy_manager.targets["Atlantic"].resources[
        'wind'].addl_curtailment == 0


def test_addl_curtailment_key_error():
    with raises(KeyError):
        atlantic_target = TargetManager('Atlantic', 0.4, 'clean',
                                        300000 * 1000)

        independent_strategy_manager = IndependentStrategyManager()
        independent_strategy_manager.add_target(atlantic_target)

        independent_strategy_manager.set_addl_curtailment({"Texas": {
            "solar": .2, "wind": .5}})
