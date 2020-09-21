# Define combinations of interconnects
interconnect_combinations = {"USA", "Texas_Western"}


# Map load zone id to state abbreviations
id2abv = {
    1: "ME",
    2: "NH",
    3: "VT",
    4: "MA",
    5: "RI",
    6: "CT",
    7: "NY",
    8: "NY",
    9: "NJ",
    10: "PA",
    11: "PA",
    12: "DE",
    13: "MD",
    14: "VA",
    15: "VA",
    16: "NC",
    17: "NC",
    18: "SC",
    19: "GA",
    20: "GA",
    21: "FL",
    22: "FL",
    23: "FL",
    24: "AL",
    25: "MS",
    26: "TN",
    27: "KY",
    28: "WV",
    29: "OH",
    30: "OH",
    31: "MI",
    32: "MI",
    33: "IN",
    34: "IL",
    35: "IL",
    36: "WI",
    37: "MN",
    38: "MN",
    39: "IA",
    40: "MO",
    41: "MO",
    42: "AR",
    43: "LA",
    44: "TX",
    45: "TX",
    46: "NM",
    47: "OK",
    48: "KS",
    49: "NE",
    50: "SD",
    51: "ND",
    52: "MT",
    201: "WA",
    202: "OR",
    203: "CA",
    204: "CA",
    205: "CA",
    206: "CA",
    207: "CA",
    208: "NV",
    209: "AZ",
    210: "UT",
    211: "NM",
    212: "CO",
    213: "WY",
    214: "ID",
    215: "MT",
    216: "TX",
    301: "TX",
    302: "TX",
    303: "TX",
    304: "TX",
    305: "TX",
    306: "TX",
    307: "TX",
    308: "TX",
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


# Map state name to load zone name
state2loadzone = {
    "Washington": {"Washington"},
    "Oregon": {"Oregon"},
    "California": {
        "Bay Area",
        "Central California",
        "Northern California",
        "Southeast California",
        "Southwest California",
    },
    "Nevada": {"Nevada"},
    "Arizona": {"Arizona"},
    "Utah": {"Utah"},
    "New Mexico": {"New Mexico Eastern", "New Mexico Western"},
    "Colorado": {"Colorado"},
    "Wyoming": {"Wyoming"},
    "Idaho": {"Idaho"},
    "Montana": {"Montana Eastern", "Montana Western"},
    "Maine": {"Maine"},
    "New Hampshire": {"New Hampshire"},
    "Vermont": {"Vermont"},
    "Massachusetts": {"Massachusetts"},
    "Rhode Island": {"Rhode Island"},
    "Connecticut": {"Connecticut"},
    "New York": {"New York City", "Upstate New York"},
    "New Jersey": {"New Jersey"},
    "Pennsylvania": {"Pennsylvania Eastern", "Pennsylvania Western"},
    "Delaware": {"Delaware"},
    "Maryland": {"Maryland"},
    "Virginia": {"Virginia Mountains", "Virginia Tidewater"},
    "North Carolina": {"North Carolina", "Western North Carolina"},
    "South Carolina": {"South Carolina"},
    "Georgia": {"Georgia North", "Georgia South"},
    "Florida": {"Florida North", "Florida Panhandle", "Florida South"},
    "Alabama": {"Alabama"},
    "Mississippi": {"Mississippi"},
    "Tennessee": {"Tennessee"},
    "Kentucky": {"Kentucky"},
    "West Virginia": {"West Virginia"},
    "Ohio": {"Ohio Lake Erie", "Ohio River"},
    "Michigan": {"Michigan Northern", "Michigan Southern"},
    "Indiana": {"Indiana"},
    "Illinois": {"Chicago North Illinois", "Illinois Downstate"},
    "Wisconsin": {"Wisconsin"},
    "Minnesota": {"Minnesota Northern", "Minnesota Southern"},
    "Iowa": {"Iowa"},
    "Missouri": {"Missouri East", "Missouri West"},
    "Arkansas": {"Arkansas"},
    "Louisiana": {"Louisiana"},
    "Texas": {
        "Coast",
        "East",
        "East Texas",
        "El Paso",
        "Far West",
        "North",
        "North Central",
        "South",
        "South Central",
        "Texas Panhandle",
        "West",
    },
    "Oklahoma": {"Oklahoma"},
    "Kansas": {"Kansas"},
    "Nebraska": {"Nebraska"},
    "South Dakota": {"South Dakota"},
    "North Dakota": {"North Dakota"},
}

# Map state abbreviations to load zone name
abv2loadzone = {
    state2abv[state]: loadzone for state, loadzone in state2loadzone.items()
}


# Map load zone name to state name
loadzone2state = {}
for state, zone_set in state2loadzone.items():
    loadzone2state.update({zone: state for zone in zone_set})


# Map interconnect name to load zone name
interconnect2loadzone = {
    "Texas": {
        "Far West",
        "North",
        "West",
        "South",
        "North Central",
        "South Central",
        "Coast",
        "East",
    },
    "Western": {
        "Washington",
        "Oregon",
        "Northern California",
        "Bay Area",
        "Central California",
        "Southwest California",
        "Southeast California",
        "Nevada",
        "Arizona",
        "Utah",
        "New Mexico Western",
        "Colorado",
        "Wyoming",
        "Idaho",
        "Montana Western",
        "El Paso",
    },
    "Eastern": {
        "Maine",
        "New Hampshire",
        "Vermont",
        "Massachusetts",
        "Rhode Island",
        "Connecticut",
        "New York City",
        "Upstate New York",
        "New Jersey",
        "Pennsylvania Eastern",
        "Pennsylvania Western",
        "Delaware",
        "Maryland",
        "Virginia Mountains",
        "Virginia Tidewater",
        "North Carolina",
        "Western North Carolina",
        "South Carolina",
        "Georgia North",
        "Georgia South",
        "Florida Panhandle",
        "Florida North",
        "Florida South",
        "Alabama",
        "Mississippi",
        "Tennessee",
        "Kentucky",
        "West Virginia",
        "Ohio River",
        "Ohio Lake Erie",
        "Michigan Northern",
        "Michigan Southern",
        "Indiana",
        "Chicago North Illinois",
        "Illinois Downstate",
        "Wisconsin",
        "Minnesota Northern",
        "Minnesota Southern",
        "Iowa",
        "Missouri East",
        "Missouri West",
        "Arkansas",
        "Louisiana",
        "East Texas",
        "Texas Panhandle",
        "New Mexico Eastern",
        "Oklahoma",
        "Kansas",
        "Nebraska",
        "South Dakota",
        "North Dakota",
        "Montana Eastern",
    },
}
interconnect2loadzone["Texas_Western"] = (
    interconnect2loadzone["Texas"] | interconnect2loadzone["Western"]
)
interconnect2loadzone["USA"] = (
    interconnect2loadzone["Eastern"]
    | interconnect2loadzone["Western"]
    | interconnect2loadzone["Texas"]
)


# Map load zone name to interconnect name
loadzone2interconnect = {
    zone: interconnect
    for interconnect, zone_set in interconnect2loadzone.items()
    for zone in zone_set
    if interconnect not in interconnect_combinations
}


# Map interconnect name to state abbreviations
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
