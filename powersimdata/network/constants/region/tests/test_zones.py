import pandas as pd
import pytest

from powersimdata.network.constants.region.zones import check_zone


def test_check_zone_argument_type():
    with pytest.raises(TypeError, match="zone must be a pandas.DataFrame"):
        check_zone("usa_tamu", 0)


def test_check_zone_index():
    zone = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}).rename_axis(index="id")
    with pytest.raises(ValueError) as excinfo:
        check_zone("usa_tamu", zone)
    assert str(excinfo.value) == "index must be named zone_id"


def test_check_zone_column():
    zone = pd.DataFrame(
        {"country": [1, 2, 3], "interconnect": [4, 5, 6], "time_zone": [7, 8, 9]}
    ).rename_axis(index="zone_id")
    with pytest.raises(ValueError) as excinfo:
        check_zone("usa_tamu", zone)
    assert str(excinfo.value) == "zone must have: abv | state | zone_name as columns"
