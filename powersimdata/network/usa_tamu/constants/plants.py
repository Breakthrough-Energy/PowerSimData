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

renewable_resources = {"solar", "wind", "wind_offshore"}
carbon_resources = {"coal", "ng", "dfo"}
clean_resources = renewable_resources | {"geothermal", "hydro", "nuclear"}
all_resources = carbon_resources | {"other"} | clean_resources


# MWh to metric tons of CO2
# Source: IPCC Special Report on Renewable Energy Sources and Climate Change
# Mitigation (2011), Annex II: Methodology, Table A.II.4, 50th percentile
# http://www.ipcc-wg3.de/report/IPCC_SRREN_Annex_II.pdf
carbon_per_mwh = {
    "coal": 1001,
    "dfo": 840,
    "ng": 469,
}

# MMBTu of fuel per hour to metric tons of CO2 per hour
# Source: https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references
# = (Heat rate MMBTu/h) * (kg C/mmbtu) * (mass ratio CO2/C) / (kg to tonnes)
carbon_per_mmbtu = {
    "coal": 26.05,
    "dfo": 20.31,
    "ng": 14.46,
}
