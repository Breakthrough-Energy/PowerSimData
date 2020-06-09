from powersimdata.input.grid import Grid
from powersimdata.input.change_table import ChangeTable

grid = Grid(["USA"])
ct = ChangeTable(grid)


def test_add_dcline_argument_type(capsys):
    capsys.readouterr()
    new_dcline = {"capacity": 500, "from_bus_id": 1, "to_bus_id": 2}
    ct.add_dcline(new_dcline)
    cap = capsys.readouterr()
    assert cap.out == "Argument enclosing new HVDC line(s) must be a list\n"
    assert ct.ct == {}
    ct.clear()


def test_add_dcline_argument_number_of_keys(capsys):
    capsys.readouterr()
    new_dcline = [{"from_bus_id": 1, "to_bus_id": 2}]
    ct.add_dcline(new_dcline)
    cap = capsys.readouterr()
    assert (
        cap.out == "Dictionary must have capacity | from_bus_id | "
        "to_bus_id as keys\n"
    )
    assert ct.ct == {}
    ct.clear()


def test_add_dcline_argument_wrong_keys(capsys):
    capsys.readouterr()
    new_dcline = [{"capacity": 1000, "from_bus": 1, "to_bus": 2}]
    ct.add_dcline(new_dcline)
    cap = capsys.readouterr()
    assert (
        cap.out == "Dictionary must have capacity | from_bus_id | "
        "to_bus_id as keys\n"
    )
    assert ct.ct == {}
    ct.clear()


def test_add_dcline_argument_wrong_bus(capsys):
    capsys.readouterr()
    new_dcline = [
        {"capacity": 2000, "from_bus_id": 300, "to_bus_id": 1000},
        {"capacity": 1000, "from_bus_id": 1, "to_bus_id": 30010010},
    ]
    ct.add_dcline(new_dcline)
    cap = capsys.readouterr()
    assert cap.out == "No bus with the following id for line #2: 30010010\n"
    assert ct.ct == {}
    ct.clear()


def test_add_dcline_argument_same_buses(capsys):
    capsys.readouterr()
    new_dcline = [{"capacity": 1000, "from_bus_id": 1, "to_bus_id": 1}]
    ct.add_dcline(new_dcline)
    cap = capsys.readouterr()
    assert cap.out == "buses of line #1 must be different\n"
    assert ct.ct == {}
    ct.clear()


def test_add_dcline_argument_negative_capacity(capsys):
    capsys.readouterr()
    new_dcline = [{"capacity": -1000, "from_bus_id": 300, "to_bus_id": 1000}]
    ct.add_dcline(new_dcline)
    cap = capsys.readouterr()
    assert cap.out == "capacity of line #1 must be positive\n"
    assert ct.ct == {}
    ct.clear()


def test_add_dcline_output():
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
    ct.clear()


def test_add_dcline_in_different_interconnect():
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
    ct.clear()


def test_add_branch_argument_buses_in_different_interconnect(capsys):
    capsys.readouterr()
    new_branch = [
        {"capacity": 2000, "from_bus_id": 300, "to_bus_id": 1000},
        {"capacity": 1000, "from_bus_id": 1, "to_bus_id": 3001001},
    ]
    ct.add_branch(new_branch)
    cap = capsys.readouterr()
    assert cap.out == "Buses of line #2 must be in same interconnect\n"
    assert ct.ct == {}
    ct.clear()


def test_add_branch_zero_distance_between_buses(capsys):
    capsys.readouterr()
    new_branch = [{"capacity": 75, "from_bus_id": 1, "to_bus_id": 3}]
    ct.add_branch(new_branch)
    cap = capsys.readouterr()
    assert cap.out == "Distance between buses of line #1 is 0\n"
    assert ct.ct == {}
    ct.clear()
