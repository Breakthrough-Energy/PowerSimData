from itertools import chain

import pandas as pd

from powersimdata.network.constants.model import model2interconnect
from powersimdata.network.helpers import interconnect_to_name, powerset

abv2country = {
    "AL": "Albania",
    "AT": "Austria",
    "BA": "Bosnia And Herzegovina",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CH": "Switzerland",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "DK": "Danemark",
    "EE": "Estonia",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GB": "Great Britain",
    "GR": "Greece",
    "HR": "Croatia",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "ME": "Montenegro",
    "MK": "Macedonia",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "RS": "Serbia",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
}

abv2timezone = {
    "AL": "ETC/GMT-1",
    "AT": "ETC/GMT-1",
    "BA": "ETC/GMT-1",
    "BE": "ETC/GMT-1",
    "BG": "ETC/GMT-2",
    "CH": "ETC/GMT-1",
    "CZ": "ETC/GMT-1",
    "DE": "ETC/GMT-1",
    "DK": "ETC/GMT-1",
    "EE": "ETC/GMT-2",
    "ES": "ETC/GMT-1",
    "FI": "ETC/GMT-2",
    "FR": "ETC/GMT-1",
    "GB": "ETC/GMT",
    "GR": "ETC/GMT-2",
    "HR": "ETC/GMT-1",
    "HU": "ETC/GMT-1",
    "IE": "ETC/GMT",
    "IT": "ETC/GMT-1",
    "LT": "ETC/GMT-2",
    "LU": "ETC/GMT-1",
    "LV": "ETC/GMT-2",
    "ME": "ETC/GMT-1",
    "MK": "ETC/GMT-1",
    "NL": "ETC/GMT-1",
    "NO": "ETC/GMT-1",
    "PL": "ETC/GMT-1",
    "PT": "ETC/GMT",
    "RO": "ETC/GMT-2",
    "RS": "ETC/GMT-1",
    "SE": "ETC/GMT-1",
    "SI": "ETC/GMT-1",
    "SK": "ETC/GMT-1",
}

interconnect2abv = {
    "ContinentalEurope": {
        "AL",
        "AT",
        "BA",
        "BE",
        "BG",
        "CH",
        "CZ",
        "DE",
        "DK",
        "ES",
        "FR",
        "GR",
        "HR",
        "HU",
        "IT",
        "LU",
        "ME",
        "MK",
        "NL",
        "PL",
        "PT",
        "RO",
        "RS",
        "SI",
        "SK",
    },
    "Nordic": {"FI", "NO", "SE"},
    "GreatBritain": {"GB"},
    "Ireland": {"IE"},
    "Baltic": {"EE", "LT", "LV"},
}
for c in powerset(model2interconnect["europe_tub"], 2):
    interconnect2abv[interconnect_to_name(c, model="europe_tub")] = set(
        chain(*[interconnect2abv[i] for i in c])
    )

name2interconnect = {
    interconnect_to_name(c, model="europe_tub"): set(c)
    for c in powerset(model2interconnect["europe_tub"], 1)
}

name2component = name2interconnect.copy()
name2component.update({"Europe": set(name2interconnect) - {"Europe"}})

interconnect2timezone = {
    interconnect_to_name(c, model="europe_tub"): "ETC/GMT-1"
    for c in powerset(model2interconnect["europe_tub"], 1)
}
interconnect2timezone.update(
    {
        interconnect_to_name("GreatBritain", model="europe_tub"): "ETC/GMT",
        interconnect_to_name("Ireland", model="europe_tub"): "ETC/GMT",
        interconnect_to_name(
            ["GreatBritain", "Ireland"], model="europe_tub"
        ): "ETC/GMT",
        interconnect_to_name("Baltic", model="europe_tub"): "ETC/GMT-2",
        interconnect_to_name(["Nordic", "Baltic"], model="europe_tub"): "ETC/GMT-2",
    }
)


def get_interconnect_mapping(zone, model):
    """Return interconnect mapping.

    :param pandas.DataFrame zone: information on zones of a grid model.
    :param str model: the grid model.
    :return: (*dict*) -- mappings of interconnect to other areas.
    """
    mapping = dict()

    name = interconnect_to_name(zone["interconnect"], model=model)

    mapping["interconnect"] = name2component[name] | {name}
    mapping["name2interconnect"] = {
        i: name2interconnect[i] for i in mapping["interconnect"]
    }
    mapping["name2component"] = {i: name2component[i] for i in mapping["interconnect"]}
    mapping["interconnect2timezone"] = {
        i: interconnect2timezone[i] for i in mapping["interconnect"]
    }
    mapping["interconnect2abv"] = {
        i: interconnect2abv[i] for i in mapping["interconnect"]
    }
    if model == "europe_tub":
        mapping["interconnect2loadzone"] = {i: set() for i in mapping["interconnect"]}
        mapping["interconnect2id"] = {i: set() for i in mapping["interconnect"]}

    return mapping


def get_country_mapping(zone, model):
    """Return country mapping.

    :param pandas.DataFrame zone: information on zones of a grid model.
    :param str model: the grid model.
    :return: (*dict*) -- mappings of countries to other areas.
    """
    mapping = dict()

    mapping["country"] = set(zone["country"])
    mapping["abv"] = set(zone["abv"])
    mapping["country_abbr"] = set(zone["abv"])
    mapping["country2abv"] = dict(zip(zone["country"], zone["abv"]))
    mapping["abv2country"] = dict(zip(zone["abv"], zone["country"]))
    mapping["abv2interconnect"] = dict(zip(zone["abv"], zone["interconnect"]))

    if model == "europe_tub":
        mapping["country2loadzone"] = {c: set() for c in set(zone["country"])}
        mapping["abv2loadzone"] = {a: set() for a in set(zone["abv"])}
        mapping["abv2id"] = {a: set() for a in set(zone["abv"])}
        mapping["id2abv"] = dict()

    return mapping


def get_loadzone_mapping(zone, model):
    """Return loadzone mapping

    :param pandas.DataFrame zone: information on zones of a grid model.
    :param str model: the grid model.
    :return: (*dict*) -- mappings of loadzones to other areas.
    """
    mapping = dict()

    if model == "europe_tub":
        mapping["loadzone"] = set()
        mapping["id2timezone"] = dict()
        mapping["id2loadzone"] = dict()
        mapping["timezone2id"] = dict()
        mapping["loadzone2id"] = dict()
        mapping["loadzone2country"] = dict()
        mapping["loadzone2abv"] = dict()
        mapping["loadzone2interconnect"] = dict()

    return mapping


def get_zones(interconnect, model):
    """Return zone constants.

    :para list interconnect: interconnect(s).
    :param str model: the grid model.
    :return: (*dict*) -- zones information.
    """
    zones = dict()
    zones["mappings"] = {"loadzone", "country", "country_abbr", "interconnect"}
    zones["division"] = "country"

    interconnect = (
        model2interconnect[model] if "Europe" in interconnect else interconnect
    )
    if model == "europe_tub":
        # geographical information will be enclosed in the PyPSA Network object
        zone_info = pd.DataFrame(
            {"abv": [a for i in interconnect for a in interconnect2abv[i]]}
        )
        zone_info["country"] = zone_info["abv"].map(abv2country)
        zone_info["time_zone"] = zone_info["abv"].map(
            {a: t for a, t in abv2timezone.items()}
        )
        zone_info["interconnect"] = zone_info["abv"].map(
            {a: i for i in interconnect for a in interconnect2abv[i]}
        )
    else:
        raise ValueError("Invalid model")

    zones.update(get_loadzone_mapping(zone_info, model))
    zones.update(get_country_mapping(zone_info, model))
    zones.update(get_interconnect_mapping(zone_info, model))

    return zones
