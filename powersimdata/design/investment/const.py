import os

inflation_rate_pct = {
    2010: 1.5,
    2011: 3.0,
    2012: 1.7,
    2013: 1.5,
    2014: 0.8,
    2015: 0.7,
    2016: 2.1,
    2017: 2.1,
    2018: 1.9,
    2019: 2.3,
    2020: 1.4,
}

hvdc_line_cost = {
    "kV": 500,
    "MW": 3500,
    "costMWmi": (3200 / 7),
}

# 2020 USD, from MISO cost estimations
hvdc_terminal_cost_per_MW = 135e3  # noqa: N816

ac_line_cost = {
    "kV": [229, 230, 230, 230, 345, 345, 345, 345, 500, 765],
    "MW": [300, 600, 900, 1200, 500, 900, 1800, 3600, 2600, 4000],
    "costMWmi": [
        3666.67,
        2000,
        1777.78,
        1500,
        39600,
        2333.33,
        1388.89,
        777.78,
        1346.15,
        1400,
    ],
}

transformer_cost = {
    "kV": [230, 345, 500, 765],
    "Cost": [5.5e6, 8.5e6, 22.75e6, 42.5e6],
}

data_dir = os.path.join(os.path.dirname(__file__), "data")
ac_reg_mult_path = os.path.join(data_dir, "LineRegMult.csv")
bus_neem_regions_path = os.path.join(data_dir, "buses_NEEMregion.csv")
bus_reeds_regions_path = os.path.join(data_dir, "buses_ReEDS_region.csv")
gen_inv_cost_path = os.path.join(data_dir, "2020-ATB-Summary_CAPEX.csv")
neem_shapefile_path = os.path.join(data_dir, "NEEM", "NEEMregions.shp")
reeds_mapping_hierarchy_path = os.path.join(data_dir, "mapping", "hierarchy.csv")
reeds_wind_csv_path = os.path.join(data_dir, "mapping", "gis_rs.csv")
reeds_wind_shapefile_path = os.path.join(data_dir, "rs", "rs.shp")
reeds_wind_to_ba_path = os.path.join(data_dir, "mapping", "region_map.csv")
regional_multiplier_path = os.path.join(data_dir, "reg_cap_cost_mult_default.csv")
transformer_cost_path = os.path.join(data_dir, "transformer_cost.csv")

gen_inv_cost_translation = {
    "OffShoreWind": "wind_offshore",
    "LandbasedWind": "wind",
    "UtilityPV": "solar",
    "Battery": "storage",
    "NaturalGas": "ng",
    "Hydropower": "hydro",
    "Nuclear": "nuclear",
    "Geothermal": "geothermal",
    "Coal": "coal",
}

gen_inv_cost_techdetails_to_keep = {
    "HydroFlash",  # Single tech for geothermal
    "NPD1",  # Single tech for hydro
    "newAvgCF",  # Single tech for coal
    "CCAvgCF",  # Single tech for ng
    "OTRG1",  # Single tech for wind_offshore
    "LTRG1",  # Single tech for wind
    "4Hr Battery Storage",  # Single tech for storage
    "Seattle",  # Single tech for solar
    "*",  # Single tech for nuclear
}

regional_multiplier_gen_translation = {
    "wind-ofs_1": "wind_offshore",
    "wind-ons_1": "wind",
    "upv_1": "solar",
    "battery": "storage",
    "Gas-CC": "ng",
    "Nuclear": "nuclear",
    "Hydro": "hydro",
    "coal-new": "coal",
}

regional_multiplier_wind_region_types = {"wind", "wind_offshore", "csp"}
regional_multiplier_ba_region_types = {
    "solar",
    "storage",
    "nuclear",
    "coal",
    "ng",
    "hydro",
    "geothermal",
}
