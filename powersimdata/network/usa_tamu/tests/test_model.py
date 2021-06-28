import pytest

from powersimdata.network.usa_tamu.model import TAMU, check_and_format_interconnect


def _assert_lists_equal(a, b):
    assert sorted(a) == sorted(b)


def test_interconnect_type():
    interconnect = 42
    with pytest.raises(TypeError):
        check_and_format_interconnect(interconnect)


def test_interconnect_value():
    interconnect = ["Canada"]
    with pytest.raises(ValueError):
        check_and_format_interconnect(interconnect)


def test_interconnect_duplicate_value():
    interconnect = ["Western", "Western", "Texas"]
    result = check_and_format_interconnect(interconnect)
    _assert_lists_equal(["Western", "Texas"], result)


def test_interconnect_usa_is_unique():
    interconnect = ["Western", "USA"]
    with pytest.raises(ValueError, match="USA cannot be paired"):
        check_and_format_interconnect(interconnect)


def test_interconnect_iterable():
    result = check_and_format_interconnect({"Texas", "Eastern"})
    _assert_lists_equal(["Eastern", "Texas"], result)

    result = check_and_format_interconnect(("Texas", "Eastern"))
    _assert_lists_equal(["Eastern", "Texas"], result)


def test_interconnect():
    arg = ("Western", ["Eastern", "Western"])
    expected = (["Western"], ["Eastern", "Western"])
    for a, e in zip(arg, expected):
        _assert_lists_equal(check_and_format_interconnect(a), e)


def _assert_interconnect_missing(interconnect, model):
    assert interconnect not in model.sub.interconnect.unique()
    assert interconnect not in model.bus2sub.interconnect.unique()
    assert interconnect not in model.bus.interconnect.unique()
    assert interconnect not in model.plant.interconnect.unique()
    assert interconnect not in model.branch.interconnect.unique()
    assert interconnect not in model.gencost["before"].interconnect.unique()
    assert interconnect not in model.gencost["after"].interconnect.unique()
    assert interconnect not in model.dcline.from_interconnect.unique()
    assert interconnect not in model.dcline.to_interconnect.unique()


def test_drop_one_interconnect():
    model = TAMU(["Western", "Texas"])
    _assert_lists_equal(["Western", "Texas"], model.interconnect)
    _assert_interconnect_missing("Eastern", model)


def test_drop_two_interconnect():
    model = TAMU(["Western"])
    _assert_lists_equal(["Western"], model.interconnect)
    for interconnect in ["Eastern", "Texas"]:
        _assert_interconnect_missing(interconnect, model)
