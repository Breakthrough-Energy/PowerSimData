import pytest

from powersimdata.network.helpers import (
    check_and_format_interconnect,
    check_model,
    interconnect_to_name,
)
from powersimdata.network.usa_tamu.model import TAMU


def _assert_lists_equal(a, b):
    assert sorted(a) == sorted(b)


def test_check_model_argument_type():
    with pytest.raises(TypeError, match="model must be a str"):
        check_model(1)


def test_check_model_argument_value():
    with pytest.raises(ValueError):
        check_model("tamu")


def test_interconnect_to_name():
    assert (
        interconnect_to_name("ContinentalEurope", model="europe_tub")
        == interconnect_to_name("Continental Europe", model="europe_tub")
        == "ContinentalEurope"
    )
    assert (
        interconnect_to_name(["Nordic", "ContinentalEurope"], model="europe_tub")
        == "ContinentalEurope_Nordic"
    )


def test_check_and_format_interconnect_argument_type():
    with pytest.raises(
        TypeError, match="interconnect must be either str or an iterable of str"
    ):
        check_and_format_interconnect(42)

    with pytest.raises(
        TypeError, match="interconnect must be either str or an iterable of str"
    ):
        check_and_format_interconnect([42, "Western"])


def test_check_and_format_interconnect_argument_value():
    interconnect = "Canada"
    with pytest.raises(ValueError):
        check_and_format_interconnect(interconnect)

    interconnect = ["Western", "USA"]
    with pytest.raises(ValueError, match="USA cannot be paired"):
        check_and_format_interconnect(interconnect, model="usa_tamu")


def test_check_and_format_interconnect():
    result = check_and_format_interconnect({"ERCOT", "Eastern"})
    _assert_lists_equal(["Eastern", "ERCOT"], result)

    result = check_and_format_interconnect(("ERCOT", "Eastern"))
    _assert_lists_equal(["Eastern", "ERCOT"], result)

    interconnect = ["Western", "Western", "Texas"]
    result = check_and_format_interconnect(interconnect, model="usa_tamu")
    _assert_lists_equal(["Western", "Texas"], result)

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
    model.build()
    _assert_lists_equal(["Western", "Texas"], model.interconnect)
    _assert_interconnect_missing("Eastern", model)


def test_drop_two_interconnect():
    model = TAMU(["Western"])
    model.build()
    _assert_lists_equal(["Western"], model.interconnect)
    for interconnect in ["Eastern", "Texas"]:
        _assert_interconnect_missing(interconnect, model)
