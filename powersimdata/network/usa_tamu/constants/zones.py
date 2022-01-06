import os
from collections import defaultdict

import pandas as pd

_exports = [
    "abv",
    "abv2id",
    "abv2interconnect",
    "abv2loadzone",
    "abv2state",
    "id2abv",
    "id2loadzone",
    "id2timezone",
    "interconnect",
    "interconnect2abv",
    "interconnect2id",
    "interconnect2loadzone",
    "interconnect2timezone",
    "interconnect_combinations",
    "loadzone",
    "loadzone2id",
    "loadzone2interconnect",
    "loadzone2state",
    "mappings",
    "state",
    "state2abv",
    "state2loadzone",
    "timezone2id",
]

mappings = {"loadzone", "state", "state_abbr", "interconnect"}

# Define combinations of interconnects
interconnect_combinations = {
    "USA": {"Eastern", "Western", "Texas"},
    "Texas_Western": {"Western", "Texas"},
}


# Map state abbreviations to state name
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


# Map state name to state abbreviations
state2abv = {value: key for key, value in abv2state.items()}


# Map zones to higher-level aggregations using the information in zone.csv
zone_csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "zone.csv")
zone_df = pd.read_csv(zone_csv_path, index_col=0)

# load zone id to load zone name
id2loadzone = zone_df["zone_name"].to_dict()
# load zone name to load zone id
loadzone2id = {v: k for k, v in id2loadzone.items()}
# Map state name to load zone name
state2loadzone = {
    k: set(v) for k, v in zone_df.groupby("state").zone_name.unique().to_dict().items()
}
# Map interconnect name to load zone name
interconnect2loadzone = {
    k: set(v)
    for k, v in zone_df.groupby("interconnect").zone_name.unique().to_dict().items()
}
interconnect2loadzone["Texas_Western"] = (
    interconnect2loadzone["Texas"] | interconnect2loadzone["Western"]
)
interconnect2loadzone["USA"] = (
    interconnect2loadzone["Eastern"]
    | interconnect2loadzone["Western"]
    | interconnect2loadzone["Texas"]
)
# Map interconnect to load zone id
interconnect2id = {
    k: set(zone_df.isin(v).query("zone_name == True").index)
    for k, v in interconnect2loadzone.items()
}

# Map load zone id to state abbreviations
id2abv = {k: state2abv[v] for k, v in zone_df.state.to_dict().items()}

# Map state abbreviations to load zone IDs
abv2id = defaultdict(set)
for k, v in id2abv.items():
    abv2id[v].add(k)

# Map state abbreviations to load zone name
abv2loadzone = {
    state2abv[state]: loadzone for state, loadzone in state2loadzone.items()
}


# Map load zone name to state name
loadzone2state = {}
for state, zone_set in state2loadzone.items():
    loadzone2state.update({zone: state for zone in zone_set})


# Map load zone name to interconnect name
loadzone2interconnect = {
    zone: interconnect
    for interconnect, zone_set in interconnect2loadzone.items()
    for zone in zone_set
    if interconnect not in interconnect_combinations
}


# Map interconnect name to state abbreviations
# Note: states which span interconnects are assigned to the one they're 'most' in.
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
    "Texas": {"TX"},
    "Western": {"WA", "OR", "CA", "NV", "AZ", "UT", "NM", "CO", "WY", "ID", "MT"},
}
interconnect2abv["USA"] = (
    interconnect2abv["Eastern"]
    | interconnect2abv["Western"]
    | interconnect2abv["Texas"]
)
interconnect2abv["Texas_Western"] = (
    interconnect2abv["Texas"] | interconnect2abv["Western"]
)


# Map state abbreviations to interconnect name
abv2interconnect = {}
for k, v in interconnect2abv.items():
    if k in interconnect_combinations:
        continue
    for s in v:
        abv2interconnect[s] = k

# List of interconnect name
interconnect = set(interconnect2abv.keys())


# List of state name
state = set(state2abv.keys())


# List of state abbreviations
abv = set(abv2state.keys())


# List of load zone name
loadzone = set(loadzone2interconnect.keys())

# Map interconnect name to time zone
interconnect2timezone = {
    "USA": "ETC/GMT+6",
    "Eastern": "ETC/GMT+5",
    "Texas": "ETC/GMT+6",
    "Western": "ETC/GMT+8",
    "Texas_Western": "ETC/GMT+7",
    "Texas_Eastern": "ETC/GMT+5",
    "Eastern_Western": "ETC/GMT+6",
}


# Map load zone IDs to time zones
# Note: load zones in > 1 time zone are put in the one where most load centers reside
id2timezone = zone_df["time_zone"].to_dict()

# Map time zones to load zone IDs
timezone2id = {k: set(v) for k, v in zone_df.groupby("time_zone").groups.items()}


def __dir__():
    return sorted(_exports)
