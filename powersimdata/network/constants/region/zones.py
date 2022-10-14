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
