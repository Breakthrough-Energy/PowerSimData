import pandas as pd

from powersimdata.network.constants.region.geography import get_geography
from powersimdata.network.helpers import get_zone_info


def from_csv(model):
    """Returns geographical and timezone information of a grid model from a CSV file.

    :param str model: grid model.
    :return: (*pandas.DataFrame*) -- a data frame with loadzone name (*'zone_name'*),
        division name (e.g. *'state'* name for USA grid models), interconnect name
        (*'interconnect'*), time zone of loadzone (*'time_zone'*), division abbreviation
        (*'abv'*) as columns and loadzone id (*'zone_id'*) as indices.
    """
    geo = get_geography(model)
    info = get_zone_info(model=model)
    info["abv"] = info[geo["division"]].map(geo[f"{geo['division']}2abv"])

    return info


def from_pypsa(model, info):
    """Returns geographical and timezone information of a grid model from a PyPSA
    Network object.

    :param str model: grid model.
    :param pd.DataFrame info: a data frame with loadzone id as index and loadzone name
        (*'zone_name'*) and division abbreviation (*'abv'*) as columns.
    :return: (*pandas.DataFrame*) -- a data frame with loadzone name (*'zone_name'*),
        division name (e.g. *'country'* name for EU grid models), interconnect name
        (*'interconnect'*), time zone of loadzone (*'time_zone'*), division abbreviation
        (*'abv'*) as columns and loadzone id (*'zone_id'*) as indices.
    """
    geo = get_geography(model)
    info[geo["division"]] = info["abv"].map(geo[f"abv2{geo['division']}"])
    info["interconnect"] = info["abv"].map(geo["abv2interconnect"])
    info["time_zone"] = info["abv"].map(geo["abv2timezone"])

    info.rename_axis(index="zone_id")

    return info


def check_zone(model, zone):
    """Validate data frame used in :class:`powersimdata.network.model.ModelImmutables`
    class.

    :param str model: grid model.
    :param pandas.DataFrame zone: data frame to be tested.
    :raises TypeError: if ``zone`` is not a pandas.DataFrame
    :raises ValueError:
        if index name is not *'zone_id'*
        if *'zone_name'*, *'state'*/*'country'* (model dependent), *'interconnect'*,
        *'time_zone'* and *'abv'* are not in columns.
    """
    if not isinstance(zone, pd.DataFrame):
        raise TypeError("zone must be a pandas.DataFrame")
    if zone.index.name != "zone_id":
        raise ValueError("index must be named zone_id")

    geo = get_geography(model)
    missing = list(
        {"zone_name", geo["division"], "interconnect", "time_zone", "abv"}
        - set(zone.columns)
    )

    if len(missing) != 0:
        raise ValueError(f"zone must have: {' | '.join(sorted(missing))} as columns")
