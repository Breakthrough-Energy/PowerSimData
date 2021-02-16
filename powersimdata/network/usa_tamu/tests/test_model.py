import pytest

from powersimdata.network.usa_tamu.model import TAMU, check_interconnect


def test_interconnect_type():
    interconnect = "Western"
    with pytest.raises(TypeError):
        check_interconnect(interconnect)


def test_interconnect_value():
    interconnect = ["Canada"]
    with pytest.raises(ValueError):
        check_interconnect(interconnect)


def test_interconnect_duplicate_value():
    interconnect = ["Western", "Western", "Texas"]
    with pytest.raises(
        ValueError, match="List of interconnects contains duplicate values"
    ):
        check_interconnect(interconnect)


def test_interconnect_usa_is_unique():
    interconnect = ["Western", "USA"]
    with pytest.raises(ValueError, match="USA cannot be paired"):
        check_interconnect(interconnect)


def test_drop_one_interconnect():
    model = TAMU(["Western", "Texas"])
    assert model.interconnect == ["Western", "Texas"]
    assert "eastern" not in model.sub.interconnect.unique()
    assert "eastern" not in model.bus2sub.interconnect.unique()
    assert "eastern" not in model.bus.interconnect.unique()
    assert "eastern" not in model.plant.interconnect.unique()
    assert "eastern" not in model.branch.interconnect.unique()
    assert "eastern" not in model.gencost["before"].interconnect.unique()
    assert "eastern" not in model.gencost["after"].interconnect.unique()
    assert "eastern" not in model.dcline.from_interconnect.unique()
    assert "eastern" not in model.dcline.to_interconnect.unique()


def test_drop_two_interconnect():
    model = TAMU(["Western"])
    assert model.interconnect == ["Western"]
    for interconnect in ["Eastern", "Texas"]:
        assert interconnect not in model.sub.interconnect.unique()
        assert interconnect not in model.bus2sub.interconnect.unique()
        assert interconnect not in model.bus.interconnect.unique()
        assert interconnect not in model.plant.interconnect.unique()
        assert interconnect not in model.branch.interconnect.unique()
        assert interconnect not in model.gencost["before"].interconnect.unique()
        assert interconnect not in model.gencost["after"].interconnect.unique()
        assert interconnect not in model.dcline.from_interconnect.unique()
        assert interconnect not in model.dcline.to_interconnect.unique()
