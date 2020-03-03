from powersimdata.scaling.clean_capacity_scaling.auto_capacity_scaling \
    import TargetManager, AbstractStrategyManager, Resource
import jsonpickle
import json


def test_create_json_of_target_object():
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

#  print(json.dumps(json.loads(jsonpickle.encode(pacific_target)),
#  indent=4, sort_keys=True))

    obj_json = json.dumps(json.loads(jsonpickle.encode(pacific_target)),
                          indent=4, sort_keys=True)
    target = jsonpickle.decode(obj_json)
    assert target.ce_target == 50000.0


def test_write_read_json_of_target_object():
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

    pacific_target.save_target_as_json()

    target = AbstractStrategyManager.load_target_from_json('Pacific')

    assert target.ce_target == 50000.0


def test_write_read_pickle_of_target_object():
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

    pacific_target.save_target_as_pickle()

    target = AbstractStrategyManager.load_target_from_pickle('Pacific')

    assert target.ce_target == 50000.0

# use json_normalize on json of resources dictionary
