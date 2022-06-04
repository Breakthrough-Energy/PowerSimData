from importlib.util import find_spec

import pytest

from powersimdata.input.converter.pypsa_to_grid import FromPyPSA
from powersimdata.input.converter.pypsa_to_profiles import (
    get_pypsa_demand_profile,
    get_pypsa_gen_profile,
)


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_extract_wind():
    import pypsa

    n = pypsa.examples.ac_dc_meshed()
    profile = get_pypsa_gen_profile(n, "wind")
    grid = FromPyPSA(n)

    assert profile.index.name == "UTC"
    assert (
        grid.plant.loc[profile.columns]["Pmax"].sum() * len(profile)
        >= profile.sum().sum()
    )


@pytest.mark.skipif(find_spec("pypsa") is None, reason="Package PyPSA not available.")
def test_extract_demand():
    import pypsa

    n = pypsa.examples.ac_dc_meshed()
    profile = get_pypsa_demand_profile(n)

    assert profile.index.name == "UTC"
    assert profile.sum().sum() >= 0
