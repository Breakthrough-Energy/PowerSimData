import pytest

from powersimdata.network.model import area_to_loadzone


def test_area_to_loadzone_argument_type():
    with pytest.raises(TypeError, match="area must be a str"):
        area_to_loadzone("usa_tamu", 3)

    with pytest.raises(TypeError, match="area_type must be either None or str"):
        area_to_loadzone("usa_tamu", "all", area_type=["interconnect"])


def test_area_to_loadzone_argument_value():
    with pytest.raises(ValueError):
        area_to_loadzone("usa_tamu", "all", area_type="province")

    with pytest.raises(ValueError, match="Invalid area / area_type combination"):
        area_to_loadzone("usa_tamu", "California", area_type="loadzone")

    with pytest.raises(ValueError, match="Invalid area / area_type combination"):
        area_to_loadzone("usa_tamu", "WA", area_type="interconnect")

    with pytest.raises(ValueError, match="Invalid area / area_type combination"):
        area_to_loadzone("usa_tamu", "Utah", area_type="state_abbr")


def test_area_to_loadzone():
    assert area_to_loadzone("usa_tamu", "El Paso") == {"El Paso"}
    assert area_to_loadzone("usa_tamu", "Texas", area_type="state") == area_to_loadzone(
        "usa_tamu", "Texas"
    )
    assert area_to_loadzone("usa_tamu", "Texas", area_type="state") == {
        "East Texas",
        "South Central",
        "Far West",
        "North Central",
        "West",
        "North",
        "Texas Panhandle",
        "South",
        "East",
        "Coast",
        "El Paso",
    }

    assert area_to_loadzone("usa_tamu", "Texas", area_type="interconnect") == {
        "South Central",
        "Far West",
        "North Central",
        "West",
        "North",
        "South",
        "East",
        "Coast",
    }
    assert area_to_loadzone("usa_tamu", "MT") == {"Montana Eastern", "Montana Western"}
