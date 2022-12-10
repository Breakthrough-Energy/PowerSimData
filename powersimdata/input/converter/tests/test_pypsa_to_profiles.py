from importlib.util import find_spec

import pytest

from powersimdata.input.converter.pypsa_to_profiles import (
    get_pypsa_demand_profile,
    get_pypsa_gen_profile,
)

if find_spec("pypsa"):
    import pypsa

    @pytest.fixture
    def network():
        return pypsa.examples.ac_dc_meshed()


def _assert_error(err_msg, error_type, func, *args, **kwargs):
    with pytest.raises(error_type) as excinfo:
        func(*args, **kwargs)
    assert err_msg in str(excinfo.value)


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_get_pypsa_gen_profile_argument_type(network):
    _assert_error(
        "network must be a Network object",
        TypeError,
        get_pypsa_gen_profile,
        "network",
        {"wind": "onwind"},
    )
    _assert_error(
        "profile2carrier must be a dict",
        TypeError,
        get_pypsa_gen_profile,
        network,
        "onwind",
    )
    _assert_error(
        "values of profile2carrier must be an iterable",
        TypeError,
        get_pypsa_gen_profile,
        network,
        {"solar": "PV"},
    )


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_get_pypsa_gen_profile_argument_value(network):
    _assert_error(
        "keys of profile2carrier must be a subset of ['hydro', 'solar', 'wind']",
        ValueError,
        get_pypsa_gen_profile,
        network,
        {"offwind": ["offwind-ac", "offwind-dc"]},
    )


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_extract_wind(network):
    gen_profile = get_pypsa_gen_profile(network, {"wind": ["wind"]})
    wind_profile = gen_profile["wind"]

    assert wind_profile.index.name == "UTC"
    assert wind_profile.columns.name is None
    assert wind_profile.sum().apply(bool).all()
    assert wind_profile.max().max() <= 1


def test_get_pypsa_demand_profile_argument_type():
    _assert_error(
        "network must be a Network object",
        TypeError,
        get_pypsa_demand_profile,
        "network",
    )


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_extract_demand(network):
    demand_profile = get_pypsa_demand_profile(network)

    assert demand_profile.index.name == "UTC"
    assert demand_profile.columns.name is None
    assert demand_profile.sum().sum() >= 0
