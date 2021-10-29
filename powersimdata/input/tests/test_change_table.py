import pytest

from powersimdata.input.change_table import ChangeTable
from powersimdata.input.grid import Grid

grid = Grid(["USA"])


@pytest.fixture
def ct():
    return ChangeTable(grid)


def test_resource_exist(ct):
    with pytest.raises(ValueError):
        ct.scale_plant_capacity("unknown", zone_name={"Idaho": 2})
    assert ct.ct == {}


def test_add_dcline_argument_type(ct):
    new_dcline = {"capacity": 500, "from_bus_id": 1, "to_bus_id": 2}
    with pytest.raises(TypeError) as excinfo:
        ct.add_dcline(new_dcline)
    assert "Argument enclosing new HVDC line(s) must be a list" in str(excinfo.value)
    assert ct.ct == {}


def test_add_dcline_argument_number_of_keys(ct):
    new_dcline = [{"from_bus_id": 1, "to_bus_id": 2}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_dcline(new_dcline)
    expected = "For new_dcline, must specify one of ('capacity', 'Pmax') but not both."
    assert expected in str(excinfo.value)
    assert ct.ct == {}


def test_add_dcline_argument_wrong_keys(ct):
    new_dcline = [{"capacity": 1000, "from_bus": 1, "to_bus": 2}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_dcline(new_dcline)
    expected_msg = "Each entry of new_dcline requires keys of: from_bus_id, to_bus_id"
    assert expected_msg in str(excinfo.value)
    assert ct.ct == {}


def test_add_dcline_argument_wrong_bus(ct):
    new_dcline = [
        {"capacity": 2000, "from_bus_id": 300, "to_bus_id": 1000},
        {"capacity": 1000, "from_bus_id": 1, "to_bus_id": 30010010},
    ]
    with pytest.raises(ValueError) as excinfo:
        ct.add_dcline(new_dcline)
    assert "No bus with the following id for line #2: 30010010" in str(excinfo.value)
    assert ct.ct == {}


def test_add_dcline_argument_same_buses(ct):
    new_dcline = [{"capacity": 1000, "from_bus_id": 1, "to_bus_id": 1}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_dcline(new_dcline)
    assert "buses of line #1 must be different" in str(excinfo.value)
    assert ct.ct == {}


def test_add_dcline_argument_negative_capacity(ct):
    new_dcline = [{"capacity": -1000, "from_bus_id": 300, "to_bus_id": 1000}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_dcline(new_dcline)
    assert "capacity of line #1 must be positive" in str(excinfo.value)
    assert ct.ct == {}


def test_add_dcline_output(ct):
    new_dcline = [
        {"capacity": 2000, "from_bus_id": 200, "to_bus_id": 2000},
        {"capacity": 1000, "from_bus_id": 9, "to_bus_id": 70042},
        {"capacity": 8000, "from_bus_id": 2008, "to_bus_id": 5997},
    ]
    ct.add_dcline(new_dcline)
    expected = {
        "new_dcline": [
            {"Pmax": 2000, "Pmin": -2000, "from_bus_id": 200, "to_bus_id": 2000},
            {"Pmax": 1000, "Pmin": -1000, "from_bus_id": 9, "to_bus_id": 70042},
            {"Pmax": 8000, "Pmin": -8000, "from_bus_id": 2008, "to_bus_id": 5997},
        ]
    }
    assert ct.ct == expected


def test_add_dcline_in_different_interconnect(ct):
    new_dcline = [
        {"capacity": 2000, "from_bus_id": 200, "to_bus_id": 2000},
        {"capacity": 8000, "from_bus_id": 2008, "to_bus_id": 3001001},
    ]
    ct.add_dcline(new_dcline)
    expected = {
        "new_dcline": [
            {"Pmax": 2000, "Pmin": -2000, "from_bus_id": 200, "to_bus_id": 2000},
            {"Pmax": 8000, "Pmin": -8000, "from_bus_id": 2008, "to_bus_id": 3001001},
        ]
    }
    assert ct.ct == expected


def test_add_dcline_Pmin_and_Pmax_success(ct):  # noqa: N802
    new_dcline = [{"Pmax": 2000, "Pmin": 0, "from_bus_id": 200, "to_bus_id": 2000}]
    ct.add_dcline(new_dcline)
    assert ct.ct == {"new_dcline": new_dcline}


def test_add_dcline_Pmin_gt_Pmax(ct):  # noqa: N802
    new_dcline = [{"Pmax": 2000, "Pmin": 3000, "from_bus_id": 200, "to_bus_id": 2000}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_dcline(new_dcline)
    assert "Pmin cannot be greater than Pmax" in str(excinfo.value)
    assert ct.ct == {}


def test_add_dcline_Pmin_and_Pmax_and_capacity(ct):  # noqa: N802
    new_dcline = [
        {"Pmax": 200, "Pmin": -200, "capacity": 10, "from_bus_id": 1, "to_bus_id": 2}
    ]
    with pytest.raises(ValueError) as excinfo:
        ct.add_dcline(new_dcline)
    expected = "For new_dcline, must specify one of ('capacity', 'Pmax') but not both"
    assert expected in str(excinfo.value)
    assert ct.ct == {}


def test_add_branch_argument_buses_in_different_interconnect(ct):
    new_branch = [
        {"capacity": 2000, "from_bus_id": 300, "to_bus_id": 1000},
        {"capacity": 1000, "from_bus_id": 1, "to_bus_id": 3001001},
    ]
    with pytest.raises(ValueError) as excinfo:
        ct.add_branch(new_branch)
    assert "Buses of line #2 must be in same interconnect" in str(excinfo.value)
    assert ct.ct == {}


def test_add_branch_zero_distance_between_buses(ct):
    new_branch = [{"capacity": 75, "from_bus_id": 1, "to_bus_id": 3}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_branch(new_branch)
    assert "Distance between buses of line #1 is 0" in str(excinfo.value)
    assert ct.ct == {}


def test_add_branch_Pmin_and_Pmax(ct):  # noqa: N802
    new_dcline = [{"Pmax": 2000, "Pmin": 0, "from_bus_id": 200, "to_bus_id": 2000}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_branch(new_dcline)
    assert "Can't independently set Pmin & Pmax for AC branches" in str(excinfo.value)
    assert ct.ct == {}


def test_add_plant_argument_type(ct):
    new_plant = {"type": "solar", "bus_id": 1, "Pmax": 100}
    with pytest.raises(TypeError) as excinfo:
        ct.add_plant(new_plant)
    assert "Argument enclosing new plant(s) must be a list" in str(excinfo.value)
    assert ct.ct == {}


def test_add_renewable_plant_missing_key_type(ct):
    new_plant = [{"bus_id": 350, "Pmax": 35}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    expected = (
        "Each entry of plant requires keys of: Pmax, bus_id, type. Missing ['type']"
    )
    assert expected in str(excinfo.value)
    assert ct.ct == {}


def test_add_renewable_plant_missing_key_bus_id(ct):
    new_plant = [{"type": "solar", "Pmax": 35}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    expected = (
        "Each entry of plant requires keys of: Pmax, bus_id, type. Missing ['bus_id']"
    )
    assert expected in str(excinfo.value)
    assert ct.ct == {}


def test_add_renewable_plant_missing_key_pmax(ct):
    new_plant = [{"type": "hydro", "bus_id": 350}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    expected = (
        "Each entry of plant requires keys of: Pmax, bus_id, type. Missing ['Pmax']"
    )
    assert expected in str(excinfo.value)
    assert ct.ct == {}


def test_add_thermal_plant_missing_key_c0(ct):
    new_plant = [{"type": "ng", "bus_id": 100, "Pmax": 75, "c1": 9, "c2": 0.25}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    assert "Missing key c0 for plant #1" in str(excinfo.value)
    assert ct.ct == {}


def test_add_thermal_plant_missing_key_c1(ct):
    new_plant = [{"type": "ng", "bus_id": 100, "Pmax": 75, "c0": 1500, "c2": 1}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    assert "Missing key c1 for plant #1" in str(excinfo.value)
    assert ct.ct == {}


def test_add_thermal_plant_missing_key_c2(ct):
    new_plant = [{"type": "ng", "bus_id": 100, "Pmax": 75, "c0": 1500, "c1": 500}]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    assert "Missing key c2 for plant #1" in str(excinfo.value)
    assert ct.ct == {}


def test_add_plant_wrong_resource(ct):
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant([{"type": "unknown", "bus_id": 50000, "Pmax": 1}])
    assert "Invalid resource: unknown" in str(excinfo.value)
    assert ct.ct == {}


def test_add_plant_wrong_bus(ct):
    new_plant = [
        {
            "type": "nuclear",
            "bus_id": 300,
            "Pmin": 500,
            "Pmax": 5000,
            "c0": 1,
            "c1": 2,
            "c2": 3,
        },
        {"type": "coal", "bus_id": 5000000, "Pmax": 200, "c0": 1, "c1": 2, "c2": 3},
    ]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    assert "No bus id 5000000 available for plant #2" in str(excinfo.value)
    assert ct.ct == {}


def test_add_thermal_plant_wrong_coefficients(ct):
    new_plant = [
        {
            "type": "ng",
            "bus_id": 300,
            "Pmin": 0,
            "Pmax": 500,
            "c0": -800,
            "c1": 30,
            "c2": 0.0025,
        }
    ]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    assert "c0 >= 0 must be satisfied for plant #1" in str(excinfo.value)
    assert ct.ct == {}


def test_add_plant_negative_pmax(ct):
    new_plant = [
        {"type": "dfo", "bus_id": 300, "Pmax": -10, "c0": 1, "c1": 2, "c2": 0.3}
    ]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    assert "Pmax >= 0 must be satisfied for plant #1" in str(excinfo.value)
    assert ct.ct == {}


def test_add_plant_negative_pmin(ct):
    new_plant = [
        {"type": "dfo", "bus_id": 300, "Pmax": 10, "c0": 100, "c1": 2, "c2": 0.1},
        {
            "type": "geothermal",
            "bus_id": 3001001,
            "Pmin": -1,
            "Pmax": 20,
            "c0": 10,
            "c1": 5,
            "c2": 1,
        },
    ]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    assert "0 <= Pmin <= Pmax must be satisfied for plant #2" in str(excinfo.value)
    assert ct.ct == {}


def test_add_plant_pmin_pmax_relationship(ct):
    new_plant = [
        {
            "type": "biomass",
            "bus_id": 13802,
            "Pmin": 30,
            "Pmax": 20,
            "c0": 30,
            "c1": 15,
            "c2": 0.1,
        }
    ]
    with pytest.raises(ValueError) as excinfo:
        ct.add_plant(new_plant)
    assert "0 <= Pmin <= Pmax must be satisfied for plant #1" in str(excinfo.value)
    assert ct.ct == {}


def test_add_plant_check_pmin_is_added(ct):
    new_plant = [
        {"type": "solar", "bus_id": 3001001, "Pmax": 85},
        {"type": "wind", "bus_id": 9, "Pmin": 5, "Pmax": 60},
        {"type": "wind_offshore", "bus_id": 13802, "Pmax": 175},
    ]
    ct.add_plant(new_plant)
    assert ct.ct["new_plant"][0]["Pmin"] == 0
    assert ct.ct["new_plant"][1]["Pmin"] == 5
    assert ct.ct["new_plant"][2]["Pmin"] == 0


def test_add_renewable_plant_check_neighbor_is_added(ct):
    new_plant = [
        {"type": "hydro", "bus_id": 3001001, "Pmin": 60, "Pmax": 85},
        {
            "type": "coal",
            "bus_id": 9,
            "Pmax": 120,
            "c0": 1000,
            "c1": 500,
            "c2": 0.3,
        },
        {"type": "wind_offshore", "bus_id": 13802, "Pmax": 175},
    ]
    ct.add_plant(new_plant)
    assert "plant_id_neighbor" in ct.ct["new_plant"][0]
    assert "plant_id_neighbor" not in ct.ct["new_plant"][1]
    assert "plant_id_neighbor" in ct.ct["new_plant"][2]


def test_add_plant_neighbor_can_be_on_same_bus(ct):
    wind_farm = grid.plant.groupby(["type"]).get_group("wind")
    hydro_plant = grid.plant.groupby(["type"]).get_group("hydro")
    bus_id_wind = wind_farm.iloc[100].bus_id
    bus_id_hydro = hydro_plant.iloc[2000].bus_id
    new_plant = [
        {"type": "wind", "bus_id": bus_id_wind, "Pmin": 60, "Pmax": 85},
        {"type": "hydro", "bus_id": bus_id_hydro, "Pmax": 175},
    ]
    ct.add_plant(new_plant)

    wind_neighbor_id = ct.ct["new_plant"][0]["plant_id_neighbor"]
    assert wind_neighbor_id == wind_farm.iloc[100].name
    hydro_neighbor_id = ct.ct["new_plant"][1]["plant_id_neighbor"]
    assert hydro_neighbor_id == hydro_plant.iloc[2000].name


def test_scale_pmin_by_plant_too_high(ct):
    ct.scale_plant_pmin("ng", plant_id={0: 100})
    assert ct.ct["ng_pmin"]["plant_id"][0] * grid.plant.loc[0, "Pmin"] == pytest.approx(
        grid.plant.loc[0, "Pmax"]
    )


def test_scale_pmin_by_zone_too_high(ct):
    ct.scale_plant_pmin("ng", zone_name={"Maine": 100})
    assert (
        ct.ct["ng_pmin"]["plant_id"][0]
        * ct.ct["ng_pmin"]["zone_id"][1]  # plant_id 0 is in Maine (zone_id 1)
        * grid.plant.loc[0, "Pmin"]
    ) == pytest.approx(grid.plant.loc[0, "Pmax"])


def test_scale_pmin_by_plant_and_zone_too_high(ct):
    ct.scale_plant_pmin("ng", plant_id={0: 10}, zone_name={"Maine": 10})
    assert (
        ct.ct["ng_pmin"]["plant_id"][0]
        * ct.ct["ng_pmin"]["zone_id"][1]  # plant_id 0 is in Maine (zone_id 1)
        * grid.plant.loc[0, "Pmin"]
    ) == pytest.approx(grid.plant.loc[0, "Pmax"])


def test_add_bus_success(ct):
    new_buses = [
        {"lat": 40, "lon": 50.5, "zone_id": 2, "baseKV": 69},
        {"lat": -40.5, "lon": -50, "zone_name": "Massachusetts", "Pd": 10},
    ]
    ct.add_bus(new_buses)
    expected_new_buses = [
        {"lat": 40, "lon": 50.5, "zone_id": 2, "Pd": 0, "baseKV": 69},
        {"lat": -40.5, "lon": -50, "zone_id": 4, "Pd": 10, "baseKV": 230},
    ]
    assert ct.ct["new_bus"] == expected_new_buses


def test_add_bus_bad_list_entries(ct):
    bad_dicts = [
        {"lat": 40, "lon": 50},  # missing zone_id/zone_name
        {"lat": 40, "zone_id": 2},  # missing lon
        {"lon": 50, "zone_id": 2},  # missing lat
        {"lat": 40, "lon": 250, "zone_id": 2},  # bad lat value
        {"lat": -100, "lon": 120, "zone_id": 2},  # bad lon value
        {"lat": "40", "lon": "50", "zone_id": 2},  # strings for lat/lon
        {"lat": 4, "lon": 5, "zone_id": 2, "zone_name": "Ohio"},  # zone_id & zone_name
        {"lat": 40, "lon": 50, "zone_id": 1000},  # bad zone_id
        {"lat": 40, "lon": 50, "zone_name": "France"},  # bad zone_name
        {"lat": 40, "lon": 50, "Pd": "100 MW"},  # bad Pd
        {"lat": 40, "lon": 50.5, "zone_id": 2, "baseKV": "69"},  # bad baseKV type
        {"lat": 40, "lon": 50.5, "zone_id": 2, "baseKV": -230},  # bad baseKV value
    ]
    for d in bad_dicts:
        with pytest.raises(ValueError):
            ct.add_bus([d])


def test_add_bus_bad_type(ct):
    with pytest.raises(TypeError):
        ct.add_bus({"bus1": {"lat": 40, "lon": 50.5, "zone_id": 2}})


def test_add_new_elements_at_new_buses(ct):
    max_existing_index = int(grid.bus.index.max())
    new_buses = [
        {"lat": 40, "lon": 50.5, "zone_id": 2, "baseKV": 69},
        {"lat": -40.5, "lon": -50, "zone_name": "Massachusetts", "Pd": 10},
    ]
    ct.add_bus(new_buses)
    new_bus1 = max_existing_index + 1
    new_bus2 = max_existing_index + 2
    ct.add_storage_capacity([{"bus_id": new_bus1, "capacity": 100}])
    ct.add_dcline([{"from_bus_id": new_bus1, "to_bus_id": new_bus2, "capacity": 200}])
    ct.add_branch([{"from_bus_id": new_bus1, "to_bus_id": new_bus2, "capacity": 300}])
    ct.add_plant([{"type": "wind", "bus_id": new_bus2, "Pmax": 400}])


def test_change_table_clear_success(ct):
    fake_scaling = {"demand", "branch", "solar", "ng_cost", "coal_pmin", "dcline"}
    fake_additions = {"storage", "new_dcline", "new_branch", "new_plant"}
    all_fakes = fake_scaling | fake_additions
    original_dict_object = ct.ct
    for fake in all_fakes:
        ct.ct[fake] = {}
    # Test that each individual clear makes a change, and the ct ends up empty
    clear_keys = {"branch", "dcline", "demand", "plant", "storage"}
    for key in clear_keys:
        old_keys = set(ct.ct.keys())
        ct.clear(key)
        assert set(ct.ct.keys()) < old_keys
    assert ct.ct == {}
    # Test that passing no args clears everything in one shot
    all_fakes = fake_scaling | fake_additions
    for fake in all_fakes:
        ct.ct[fake] = {}
    ct.clear()
    assert ct.ct == {}
    assert ct.ct is original_dict_object


def test_change_table_clear_bad_type(ct):
    with pytest.raises(TypeError):
        ct.clear(["plant"])


def test_change_table_clear_bad_key(ct):
    with pytest.raises(ValueError):
        ct.clear({"plantttt"})


def test_remove_branch(ct):
    ct.remove_branch({0})
    with pytest.raises(ValueError):
        # Can't remove again, because it shouldn't exist
        ct.remove_branch({0})


def test_remove_bus(ct):
    with pytest.raises(ValueError):
        # Can't remove, because there are branches attached to it
        ct.remove_bus({1})
    ct.remove_branch({0, 1, 2})
    ct.remove_bus({1})
    with pytest.raises(ValueError):
        # Can't remove again, because it shouldn't exist
        ct.remove_bus({1})
    # Evan after we remove the branch connected to bus 845...
    ct.remove_branch({1094})
    with pytest.raises(ValueError):
        # We can't remove this bus, since there's a generator with non-zero capacity
        ct.remove_bus({845})
    ct.scale_plant_capacity(resource="ng", plant_id={0: 0})
    ct.remove_bus({845})
