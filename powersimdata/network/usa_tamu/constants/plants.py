id2type = {
    0: "wind",
    1: "solar",
    2: "hydro",
    3: "ng",
    4: "nuclear",
    5: "coal",
    6: "geothermal",
    7: "dfo",
    8: "biomass",
    9: "other",
    10: "storage",
    11: "wind_offshore",
}

type2id = {value: key for key, value in id2type.items()}

type2color = {
    "wind": "xkcd:green",
    "solar": "xkcd:amber",
    "hydro": "xkcd:light blue",
    "ng": "xkcd:orchid",
    "nuclear": "xkcd:silver",
    "coal": "xkcd:light brown",
    "geothermal": "xkcd:hot pink",
    "dfo": "xkcd:royal blue",
    "biomass": "xkcd:dark green",
    "other": "xkcd:melon",
    "storage": "xkcd:orange",
    "wind_offshore": "xkcd:teal",
}

type2label = {
    "nuclear": "Nuclear",
    "geothermal": "Geo-thermal",
    "coal": "Coal",
    "dfo": "DFO",
    "hydro": "Hydro",
    "ng": "Natural Gas",
    "solar": "Solar",
    "wind": "Wind",
    "wind_offshore": "Wind Offshore",
    "biomass": "Biomass",
    "other": "Other",
    "storage": "Storage",
}

label2type = {value: key for key, value in type2label.items()}
