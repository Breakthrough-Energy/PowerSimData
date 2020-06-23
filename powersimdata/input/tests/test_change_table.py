import pytest

from powersimdata.input.grid import Grid
from powersimdata.input.change_table import ChangeTable


grid = Grid(["USA"])
ct = ChangeTable(grid)


def test_resource_exist(capsys):
    try:
        with pytest.raises(ValueError):
            ct.scale_plant_capacity("unknown", zone_name={"Idaho": 2})
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_dcline_argument_type(capsys):
    try:
        capsys.readouterr()
        new_dcline = {"capacity": 500, "from_bus_id": 1, "to_bus_id": 2}
        ct.add_dcline(new_dcline)
        cap = capsys.readouterr()
        assert cap.out == "Argument enclosing new HVDC line(s) must be a list\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_dcline_argument_number_of_keys(capsys):
    try:
        capsys.readouterr()
        new_dcline = [{"from_bus_id": 1, "to_bus_id": 2}]
        ct.add_dcline(new_dcline)
        cap = capsys.readouterr()
        assert (
            cap.out == "Dictionary must have capacity | from_bus_id | "
            "to_bus_id as keys\n"
        )
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_dcline_argument_wrong_keys(capsys):
    try:
        capsys.readouterr()
        new_dcline = [{"capacity": 1000, "from_bus": 1, "to_bus": 2}]
        ct.add_dcline(new_dcline)
        cap = capsys.readouterr()
        assert (
            cap.out == "Dictionary must have capacity | from_bus_id | "
            "to_bus_id as keys\n"
        )
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_dcline_argument_wrong_bus(capsys):
    try:
        capsys.readouterr()
        new_dcline = [
            {"capacity": 2000, "from_bus_id": 300, "to_bus_id": 1000},
            {"capacity": 1000, "from_bus_id": 1, "to_bus_id": 30010010},
        ]
        ct.add_dcline(new_dcline)
        cap = capsys.readouterr()
        assert cap.out == "No bus with the following id for line #2: 30010010\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_dcline_argument_same_buses(capsys):
    try:
        capsys.readouterr()
        new_dcline = [{"capacity": 1000, "from_bus_id": 1, "to_bus_id": 1}]
        ct.add_dcline(new_dcline)
        cap = capsys.readouterr()
        assert cap.out == "buses of line #1 must be different\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_dcline_argument_negative_capacity(capsys):
    try:
        capsys.readouterr()
        new_dcline = [{"capacity": -1000, "from_bus_id": 300, "to_bus_id": 1000}]
        ct.add_dcline(new_dcline)
        cap = capsys.readouterr()
        assert cap.out == "capacity of line #1 must be positive\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_dcline_output():
    try:
        new_dcline = [
            {"capacity": 2000, "from_bus_id": 200, "to_bus_id": 2000},
            {"capacity": 1000, "from_bus_id": 9, "to_bus_id": 70042},
            {"capacity": 8000, "from_bus_id": 2008, "to_bus_id": 5997},
        ]
        ct.add_dcline(new_dcline)
        expected = {
            "new_dcline": [
                {"capacity": 2000, "from_bus_id": 200, "to_bus_id": 2000},
                {"capacity": 1000, "from_bus_id": 9, "to_bus_id": 70042},
                {"capacity": 8000, "from_bus_id": 2008, "to_bus_id": 5997},
            ]
        }
        assert ct.ct == expected
    finally:
        ct.clear()


def test_add_dcline_in_different_interconnect():
    try:
        new_dcline = [
            {"capacity": 2000, "from_bus_id": 200, "to_bus_id": 2000},
            {"capacity": 8000, "from_bus_id": 2008, "to_bus_id": 3001001},
        ]
        ct.add_dcline(new_dcline)
        expected = {
            "new_dcline": [
                {"capacity": 2000, "from_bus_id": 200, "to_bus_id": 2000},
                {"capacity": 8000, "from_bus_id": 2008, "to_bus_id": 3001001},
            ]
        }
        assert ct.ct == expected
    finally:
        ct.clear()


def test_add_branch_argument_buses_in_different_interconnect(capsys):
    try:
        capsys.readouterr()
        new_branch = [
            {"capacity": 2000, "from_bus_id": 300, "to_bus_id": 1000},
            {"capacity": 1000, "from_bus_id": 1, "to_bus_id": 3001001},
        ]
        ct.add_branch(new_branch)
        cap = capsys.readouterr()
        assert cap.out == "Buses of line #2 must be in same interconnect\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_branch_zero_distance_between_buses(capsys):
    try:
        capsys.readouterr()
        new_branch = [{"capacity": 75, "from_bus_id": 1, "to_bus_id": 3}]
        ct.add_branch(new_branch)
        cap = capsys.readouterr()
        assert cap.out == "Distance between buses of line #1 is 0\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_plant_argument_type(capsys):
    try:
        capsys.readouterr()
        new_plant = {"type": "solar", "bus_id": 1, "Pmax": 100}
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Argument enclosing new plant(s) must be a list\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_renewable_plant_missing_key_type(capsys):
    try:
        capsys.readouterr()
        new_plant = [{"bus_id": 350, "Pmax": 35}]
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Missing key type for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_renewable_plant_missing_key_bus_id(capsys):
    try:
        capsys.readouterr()
        new_plant = [{"type": "solar", "Pmax": 35}]
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Missing key bus_id for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_renewable_plant_missing_key_pmax(capsys):
    try:
        capsys.readouterr()
        new_plant = [{"type": "hydro", "bus_id": 350}]
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Missing key Pmax for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_thermal_plant_missing_key_c0(capsys):
    try:
        capsys.readouterr()
        new_plant = [{"type": "ng", "bus_id": 100, "Pmax": 75, "c1": 9, "c2": 0.25}]
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Missing key c0 for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_thermal_plant_missing_key_c1(capsys):
    try:
        capsys.readouterr()
        new_plant = [{"type": "ng", "bus_id": 100, "Pmax": 75, "c0": 1500, "c2": 1}]
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Missing key c1 for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_thermal_plant_missing_key_c2(capsys):
    try:
        capsys.readouterr()
        new_plant = [{"type": "ng", "bus_id": 100, "Pmax": 75, "c0": 1500, "c1": 500}]
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Missing key c2 for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_renewable_plant_wrong_key(capsys):
    try:
        capsys.readouterr()
        new_plant = [{"type": "wind", "bus": 150, "Pmax": 15}]
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Missing key bus_id for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_plant_wrong_resource():
    try:
        ct.add_plant([{"type": "unknown", "bus_id": 50000, "Pmax": 1}])
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_plant_wrong_bus(capsys):
    try:
        capsys.readouterr()
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
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "No bus id 5000000 available for plant #2\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_thermal_plant_wrong_coefficients(capsys):
    try:
        capsys.readouterr()
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
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "c0 >= 0 must be satisfied for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_plant_negative_pmax(capsys):
    try:
        capsys.readouterr()
        new_plant = [
            {"type": "dfo", "bus_id": 300, "Pmax": -10, "c0": 1, "c1": 2, "c2": 0.3}
        ]
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "Pmax >= 0 must be satisfied for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_plant_negative_pmin(capsys):
    try:
        capsys.readouterr()
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
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "0 <= Pmin <= Pmax must be satisfied for plant #2\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_plant_pmin_pmax_relationship(capsys):
    try:
        capsys.readouterr()
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
        ct.add_plant(new_plant)
        cap = capsys.readouterr()
        assert cap.out == "0 <= Pmin <= Pmax must be satisfied for plant #1\n"
        assert ct.ct == {}
    finally:
        ct.clear()


def test_add_plant_check_pmin_is_added():
    try:
        new_plant = [
            {"type": "solar", "bus_id": 3001001, "Pmax": 85},
            {"type": "wind", "bus_id": 9, "Pmin": 5, "Pmax": 60},
            {"type": "wind_offshore", "bus_id": 13802, "Pmax": 175},
        ]
        ct.add_plant(new_plant)
        assert ct.ct["new_plant"][0]["Pmin"] == 0
        assert ct.ct["new_plant"][1]["Pmin"] == 5
        assert ct.ct["new_plant"][2]["Pmin"] == 0
    finally:
        ct.clear()


def test_add_renewable_plant_check_neighbor_is_added():
    try:
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
    finally:
        ct.clear()


def test_add_plant_neighbor_can_be_on_same_bus():
    wind_farm = grid.plant.groupby(["type"]).get_group("wind")
    hydro_plant = grid.plant.groupby(["type"]).get_group("hydro")
    try:
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
    finally:
        ct.clear()
