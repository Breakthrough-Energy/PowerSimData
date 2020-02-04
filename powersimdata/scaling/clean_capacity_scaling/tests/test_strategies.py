from prereise.scaling.clean_capacity_scaling.auto_capacity_scaling import Resource, TargetManager, CollaborativeManager, AbstractStrategy
from pytest import approx

def test_independent_capacity_strategy():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.25)
    solar.set_generation(8125)
    solar.set_curtailment(0)
    solar.set_addl_curtailment(0.40)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.4)
    wind.set_generation(12649)
    wind.set_curtailment(0)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)

    prev_CE_generation = target.calculate_prev_ce_generation()
    CE_shortfall = target.calculate_ce_shortfall(28774.16, 0)
    solar_added, wind_added = target.calculate_added_capacity()
    assert wind_added == approx(4360.459)
    assert solar_added == approx(4481.582)


def test_independent_capacity_strategy_Atlantic_2():
    solar = Resource('solar', 3)
    solar.set_capacity(0.3, 4200, 0.3)
    solar.set_generation(11067.84)
    solar.set_curtailment(0)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.35, 4100, 0.35)
    wind.set_generation(12605.04)
    wind.set_curtailment(0)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4500, 1)
    geo.set_generation(8500)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 4400, 1)
    hydro.set_generation(7500)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 4300, 1)
    nuclear.set_generation(6500)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Atlantic', 0.3, 'renewables', 300000)
    target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    prev_CE_generation = target.calculate_prev_ce_generation()
#     assert prev_CE_generation == approx(39672.88)
    CE_shortfall = target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(39672.88, 0)
#     assert CE_shortfall == approx(50327.12)

    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(8928.948)
    assert wind_added == approx(8716.354)


def test_independent_capacity_strategy_Pacific_3():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6000)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    prev_CE_generation = target.calculate_prev_ce_generation()
#     assert prev_CE_generation == approx(26000)
    CE_shortfall = target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(26000, 0)
#     assert CE_shortfall == approx(24000)

    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(4933.333)
    assert wind_added == approx(4800)


def test_independent_capacity_strategy_Atlantic_4():
    solar = Resource('solar', 3)
    solar.set_capacity(0.3, 4200, 0.284608)
    solar.set_generation(10500)
    solar.set_curtailment(0.051305)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.35, 4100, 0.319317)
    wind.set_generation(11500)
    wind.set_curtailment(0.087667)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4500, 1)
    geo.set_generation(8500)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 4400, 1)
    hydro.set_generation(7500)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 4300, 1)
    nuclear.set_generation(6500)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Atlantic', 0.4, 'clean', 300000)
    target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro', 'nuclear'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    prev_CE_generation = target.calculate_prev_ce_generation()
#     assert prev_CE_generation == approx(44500)
    CE_shortfall = target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(44500, 0)
#     assert CE_shortfall == approx(75500)

    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(14413.636)
    assert wind_added == approx(14070.455)


def test_independent_capacity_strategy_Pacific_external_6():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    prev_CE_generation = target.calculate_prev_ce_generation()
#     assert prev_CE_generation == 26000
    CE_shortfall = target.calculate_ce_shortfall(prev_CE_generation, 40000)
#     CE_shortfall = target.CalculateCEShortfall(26000, 40000)
#     assert CE_shortfall == approx(10000)
    solar_added, wind_added = target.calculate_added_capacity()
    assert solar_added == approx(2055.556)
    assert wind_added == approx(2000)


def test_independent_capacity_strategy_Pacific_solar0_7():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    prev_CE_generation = target.calculate_prev_ce_generation()
#     assert prev_CE_generation == 26000
    CE_shortfall = target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(26000, 0)
#     assert CE_shortfall == approx(24000)
    solar_added, wind_added = target.calculate_added_capacity(0)
    assert solar_added == approx(0)
    assert wind_added == approx(7854.545)


def test_independent_capacity_strategy_Pacific_solar75_8():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    prev_CE_generation = target.calculate_prev_ce_generation()
#     assert prev_CE_generation == 26000
    CE_shortfall = target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(26000, 0)
#     assert CE_shortfall == approx(24000)
    solar_added, wind_added = target.calculate_added_capacity(0.75)
    assert solar_added == approx(8246.26)
    assert wind_added == approx(2748.753)


def test_independent_capacity_strategy_Pacific_solar100_9():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379314)
    solar.set_generation(7000)
    solar.set_curtailment(0.138482745)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347854685)
    wind.set_generation(11000)
    wind.set_curtailment(0.130363287)
    wind.set_addl_curtailment(0)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    prev_CE_generation = target.calculate_prev_ce_generation()
#     assert prev_CE_generation == 26000
    CE_shortfall = target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(26000, 0)
#     assert CE_shortfall == approx(24000)
    solar_added, wind_added = target.calculate_added_capacity(1)
    assert solar_added == approx(12685.714)
    assert wind_added == 0


def test_independent_capacity_strategy_windcurtail_10():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.215379)
    solar.set_generation(7000)
    solar.set_curtailment(0.138483)
    solar.set_addl_curtailment(0)

    wind = Resource('wind', 3)
    wind.set_capacity(0.4, 3600, 0.347855)
    wind.set_generation(11000)
    wind.set_curtailment(0.130363)
    wind.set_addl_curtailment(0.15)

    geo = Resource('geo', 3)
    geo.set_capacity(1, 4000, 1)
    geo.set_generation(8000)
    geo.set_curtailment(0)
    geo.set_addl_curtailment(0)

    hydro = Resource('hydro', 3)
    hydro.set_capacity(1, 3900, 1)
    hydro.set_generation(7000)
    hydro.set_curtailment(0)
    hydro.set_addl_curtailment(0)

    nuclear = Resource('nuclear', 3)
    nuclear.set_capacity(1, 3800, 1)
    nuclear.set_generation(6500)
    nuclear.set_curtailment(0)
    nuclear.set_addl_curtailment(0)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.set_allowed_resources(['solar', 'wind', 'geo'])
    target.add_resource(solar)
    target.add_resource(wind)
    target.add_resource(geo)
    target.add_resource(hydro)
    target.add_resource(nuclear)

    prev_CE_generation = target.calculate_prev_ce_generation()
#     assert prev_CE_generation == 26000
    CE_shortfall = target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(26000, 0)
#     assert CE_shortfall == approx(24000)
    solar_added, wind_added = target.calculate_added_capacity(0.75)
    assert solar_added == approx(8703.117)
    assert wind_added == approx(2901.039)


def test_collaborative_capacity_strategy():
    # create Pacific
    pacific_solar = Resource('solar', 3)
    pacific_solar.set_capacity(0.25, 3700, 0.215379)
    pacific_solar.set_generation(7000)
    pacific_solar.set_curtailment(0.138483)
    pacific_solar.set_addl_curtailment(0)

    pacific_wind = Resource('wind', 3)
    pacific_wind.set_capacity(0.4, 3600, 0.347855)
    pacific_wind.set_generation(11000)
    pacific_wind.set_curtailment(0.130363)
    pacific_wind.set_addl_curtailment(0)

    pacific_geo = Resource('geo', 3)
    pacific_geo.set_capacity(1, 4000, 1)
    pacific_geo.set_generation(8000)
    pacific_geo.set_curtailment(0)
    pacific_geo.set_addl_curtailment(0)

    pacific_hydro = Resource('hydro', 3)
    pacific_hydro.set_capacity(1, 3900, 1)
    pacific_hydro.set_generation(7000)
    pacific_hydro.set_curtailment(0)
    pacific_hydro.set_addl_curtailment(0)

    pacific_nuclear = Resource('nuclear', 3)
    pacific_nuclear.set_capacity(1, 4300, 1)
    pacific_nuclear.set_generation(6500)
    pacific_nuclear.set_curtailment(0)
    pacific_nuclear.set_addl_curtailment(0)

    pacific_target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    pacific_target.set_allowed_resources(['solar', 'wind', 'geo'])
    pacific_target.add_resource(pacific_solar)
    pacific_target.add_resource(pacific_wind)
    pacific_target.add_resource(pacific_geo)
    pacific_target.add_resource(pacific_hydro)
    pacific_target.add_resource(pacific_nuclear)

    prev_CE_generation = pacific_target.calculate_prev_ce_generation()
#     assert prev_CE_generation == approx(26000)
    CE_shortfall = pacific_target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(26000, 0)
#     assert CE_shortfall == approx(24000)

    # create Atlantic
    atlantic_solar = Resource('solar', 3)
    atlantic_solar.set_capacity(0.3, 4200, 0.284608)
    atlantic_solar.set_generation(10500)
    atlantic_solar.set_curtailment(0.051305)
    atlantic_solar.set_addl_curtailment(0)

    atlantic_wind = Resource('wind', 3)
    atlantic_wind.set_capacity(0.35, 4100, 0.319317)
    atlantic_wind.set_generation(11500)
    atlantic_wind.set_curtailment(0.087667)
    atlantic_wind.set_addl_curtailment(0)

    atlantic_geo = Resource('geo', 3)
    atlantic_geo.set_capacity(1, 4500, 1)
    atlantic_geo.set_generation(8500)
    atlantic_geo.set_curtailment(0)
    atlantic_geo.set_addl_curtailment(0)

    atlantic_hydro = Resource('hydro', 3)
    atlantic_hydro.set_capacity(1, 4400, 1)
    atlantic_hydro.set_generation(7500)
    atlantic_hydro.set_curtailment(0)
    atlantic_hydro.set_addl_curtailment(0)

    atlantic_nuclear = Resource('nuclear', 3)
    atlantic_nuclear.set_capacity(1, 4300, 1)
    atlantic_nuclear.set_generation(6500)
    atlantic_nuclear.set_curtailment(0)
    atlantic_nuclear.set_addl_curtailment(0)

    atlantic_target = TargetManager('Atlantic', 0.4, 'clean', 300000)
    atlantic_target.set_allowed_resources(['solar', 'wind', 'geo', 'hydro', 'nuclear'])
    atlantic_target.add_resource(atlantic_solar)
    atlantic_target.add_resource(atlantic_wind)
    atlantic_target.add_resource(atlantic_geo)
    atlantic_target.add_resource(atlantic_hydro)
    atlantic_target.add_resource(atlantic_nuclear)

    prev_CE_generation = atlantic_target.calculate_prev_ce_generation()
    assert prev_CE_generation == approx(44500)
    CE_shortfall = atlantic_target.calculate_ce_shortfall(prev_CE_generation, 0)
#     CE_shortfall = target.CalculateCEShortfall(44500, 0)
    assert CE_shortfall == approx(75500)

    collab = CollaborativeManager()
    collab.add_target(pacific_target)
    collab.add_target(atlantic_target)

    collab_CE_shortfall = collab.calculate_total_shortfall()
    assert collab_CE_shortfall == approx(99500)
    collab_prev_CE_generation = collab.calculate_total_prev_ce_generation()
    assert collab_prev_CE_generation == approx(70500)

    solar_added, wind_added = collab.calculate_added_capacity()
    assert solar_added == approx(19651.25)
    assert wind_added == approx(19153.75)

    solar_cap_scaling, wind_cap_scaling = collab.calculate_capacity_scaling()
    assert(solar_cap_scaling == wind_cap_scaling)
    assert collab.targets['Pacific'].resources['solar'].prev_capacity*solar_cap_scaling == approx(9203.75)
    assert collab.targets['Pacific'].resources['wind'].prev_capacity*wind_cap_scaling == approx(8955)
    assert collab.targets['Atlantic'].resources['solar'].prev_capacity*solar_cap_scaling == approx(10447.5)
    assert collab.targets['Atlantic'].resources['wind'].prev_capacity*wind_cap_scaling == approx(10198.75)