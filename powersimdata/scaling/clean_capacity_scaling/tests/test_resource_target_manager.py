from prereise.scaling.clean_capacity_scaling.auto_capacity_scaling import Resource, TargetManager
from pytest import approx


def test_logic():
    assert 1 == 1


def test_expected_cap_factor():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.25)
    solar.set_generation(8125)
    solar.set_curtailment(0)
    solar.set_addl_curtailment(0.40)

    result = solar.calculate_expected_cap_factor()
    assert result == 0.15


def test_calculate_next_capacity():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.25)
    solar.set_generation(8125)
    solar.set_curtailment(0)
    solar.set_addl_curtailment(0.40)

    result = solar.calculate_next_capacity(4482)
    assert result == 8182


def test_calculate_ce_target():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    assert target.CE_target == 50000


def test_calculate_ce_shortfall_prev_gt_external():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    result = target.calculate_ce_shortfall(28774.16, 0)
    assert result == approx(21225.84)


def test_calculate_ce_shortfall_external_gt_prev():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    result = target.calculate_ce_shortfall(28774.16, 40000)
    assert result == 10000


def test_calculate_ce_no_shortfall_prev_gt_external():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    result = target.calculate_ce_shortfall(68774.16, 56000)
    assert result == 0


def test_calculate_ce_no_shortfall_external_gt_prev():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    result = target.calculate_ce_shortfall(68774.16, 70000)
    assert result == 0


def test_calculate_ce_overgeneration_prev_gt_external():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    result = target.calculate_ce_overgeneration(28774.16, 0)
    assert result == 0


def test_calculate_ce_overgeneration_external_gt_prev():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    result = target.calculate_ce_overgeneration(28774.16, 40000)
    assert result == 0

def test_calculate_ce_no_overgeneration_prev_gt_external():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    result = target.calculate_ce_overgeneration(68774.16, 56000)
    assert result == approx(18774.16)


def test_calculate_ce_no_overgeneration_external_gt_prev():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    result = target.calculate_ce_overgeneration(68774.16, 70000)
    assert result == 20000


def test_add_resource_solar():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.25)
    solar.set_generation(8125)
    solar.set_curtailment(0)
    solar.set_addl_curtailment(0.40)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.add_resource(solar)
    
    assert target.resources['solar'] == solar


def test_cal_prev_solar():
    solar = Resource('solar', 3)
    solar.set_capacity(0.25, 3700, 0.25)
    solar.set_generation(8125)
    solar.set_curtailment(0)
    solar.set_addl_curtailment(0.40)

    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    target.allowed_resources = ['solar']
    target.add_resource(solar)

    result = target.calculate_prev_ce_generation()
    assert result == 8125


def test_cal_prev_Pacific():
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

    result = target.calculate_prev_ce_generation()
    assert result == 28774


def test_set_allowed_resources():
    target = TargetManager('Pacific', 0.25, 'renewables', 200000)
    allowed_resources = ['solar','wind', 'geo']
    target.set_allowed_resources(allowed_resources)
    assert target.allowed_resources == allowed_resources