import ast
from itertools import chain

from powersimdata.network.constants.model import model2interconnect
from powersimdata.network.helpers import get_zone_info, interconnect_to_name, powerset

abv2state = {
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
}

interconnect2abv = {
    "Eastern": {
        "ME",
        "NH",
        "VT",
        "MA",
        "RI",
        "CT",
        "NY",
        "NJ",
        "PA",
        "DE",
        "MD",
        "VA",
        "NC",
        "SC",
        "GA",
        "FL",
        "AL",
        "MS",
        "TN",
        "KY",
        "WV",
        "OH",
        "MI",
        "IN",
        "IL",
        "WI",
        "MN",
        "IA",
        "MO",
        "AR",
        "LA",
        "OK",
        "KS",
        "NE",
        "SD",
        "ND",
    },
    "ERCOT": {"TX"},
    "Western": {"WA", "OR", "CA", "NV", "AZ", "UT", "NM", "CO", "WY", "ID", "MT"},
}
for c in powerset(model2interconnect["hifld"], 2):
    interconnect2abv[interconnect_to_name(c, model="hifld")] = set(
        chain(*[interconnect2abv[i] for i in c])
    )

name2interconnect = {
    interconnect_to_name(c, model="hifld"): set(c)
    for c in powerset(model2interconnect["hifld"], 1)
}

name2component = name2interconnect.copy()
name2component.update({"USA": set(name2interconnect) - {"USA"}})

interconnect2timezone = {
    interconnect_to_name("USA"): "ETC/GMT+6",
    interconnect_to_name("Eastern"): "ETC/GMT+5",
    interconnect_to_name("ERCOT"): "ETC/GMT+6",
    interconnect_to_name("Western"): "ETC/GMT+8",
    interconnect_to_name(["ERCOT", "Western"]): "ETC/GMT+7",
    interconnect_to_name(["ERCOT", "Eastern"]): "ETC/GMT+5",
    interconnect_to_name(["Eastern", "Western"]): "ETC/GMT+6",
}


def get_interconnect_mapping(zone, model):
    """Return interconnect mapping.

    :param pandas.DataFrame zone: information on zones of a grid model.
    :param str model: the grid model.
    :return: (*dict*) -- mappings of interconnect to other areas.
    """

    def _substitute(entry):
        return {
            i: ast.literal_eval(repr(entry).replace("ERCOT", sub))[i]
            for i in mapping["interconnect"]
        }

    mapping = dict()
    sub = "Texas" if model == "usa_tamu" else "ERCOT"

    name = interconnect_to_name(zone["interconnect"].unique(), model=model)
    mapping["interconnect"] = ast.literal_eval(
        repr(name2component).replace("ERCOT", sub)
    )[name] | {name}
    mapping["name2interconnect"] = _substitute(name2interconnect)
    mapping["name2component"] = _substitute(name2component)
    mapping["interconnect2timezone"] = _substitute(interconnect2timezone)
    mapping["interconnect2abv"] = _substitute(interconnect2abv)
    mapping["interconnect2loadzone"] = {
        i: set(l)
        for i, l in zone.set_index("zone_name").groupby("interconnect").groups.items()
    }
    mapping["interconnect2id"] = {
        i: set(id) for i, id in zone.groupby("interconnect").groups.items()
    }

    return mapping


def get_state_mapping(zone):
    """Return state mapping.

    :param pandas.DataFrame zone: information on zones of a grid model.
    :return: (*dict*) -- mappings of states to other areas.
    """
    mapping = dict()

    mapping["state"] = set(zone["state"])
    mapping["abv"] = set(zone["abv"])
    mapping["state_abbr"] = set(zone["abv"])
    mapping["state2loadzone"] = {
        k: set(v)
        for k, v in zone.groupby("state")["zone_name"].unique().to_dict().items()
    }
    mapping["abv2loadzone"] = {
        k: set(v)
        for k, v in zone.groupby("abv")["zone_name"].unique().to_dict().items()
    }
    mapping["abv2id"] = {k: set(v) for k, v in zone.groupby("abv").groups.items()}
    mapping["id2abv"] = {k: v for k, v in zone["abv"].to_dict().items()}
    mapping["state2abv"] = dict(zip(zone["state"], zone["abv"]))
    mapping["abv2state"] = dict(zip(zone["abv"], zone["state"]))
    mapping["abv2interconnect"] = dict(zip(zone["abv"], zone["interconnect"]))

    return mapping


def get_loadzone_mapping(zone):
    """Return loadzone mapping

    :param pandas.DataFrame zone: information on zones of a grid model.
    :return: (*dict*) -- mappings of loadzones to other areas
    """
    mapping = dict()

    mapping["loadzone"] = set(zone["zone_name"])
    mapping["id2timezone"] = zone["time_zone"].to_dict()
    mapping["id2loadzone"] = zone["zone_name"].to_dict()
    mapping["timezone2id"] = {
        t: set(i) for t, i in zone.groupby("time_zone").groups.items()
    }
    mapping["loadzone2id"] = {
        l: i[0] for l, i in zone.groupby("zone_name").groups.items()
    }
    mapping["loadzone2state"] = dict(zip(zone["zone_name"], zone["state"]))
    mapping["loadzone2abv"] = dict(zip(zone["zone_name"], zone["abv"]))
    mapping["loadzone2interconnect"] = dict(
        zip(zone["zone_name"], zone["interconnect"])
    )

    return mapping


def get_zones(interconnect, model):
    """Return zone constants.

    :para list interconnect: interconnect(s).
    :param str model: the grid model.
    :return: (*dict*) -- zones information.
    """
    interconnect = (  # noqa
        model2interconnect[model] if "USA" in interconnect else interconnect
    )
    zone_info = get_zone_info(model=model).query("interconnect == @interconnect")
    zone_info["abv"] = zone_info["state"].map({s: a for a, s in abv2state.items()})

    zones = dict()
    zones["mappings"] = {"loadzone", "state", "state_abbr", "interconnect"}
    zones["division"] = "state"

    zones.update(get_loadzone_mapping(zone_info))
    zones.update(get_state_mapping(zone_info))
    zones.update(get_interconnect_mapping(zone_info, model))

    return zones
