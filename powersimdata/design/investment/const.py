import os

hvdc_line_cost = {
    "kV": 500,
    "MW": 3500,
    "costMWmi": (3200 / 7),
}

hvdc_terminal_cost = 550e6

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

data_dir = os.path.join(os.path.dirname(__file__), "Data")
ac_reg_mult_path = os.path.join(data_dir, "LineRegMult.csv")
bus_regions_path = os.path.join(data_dir, "buses_NEEMregion.csv")
gen_inv_cost_path = os.path.join(data_dir, "2020-ATB-Summary_CAPEX.csv")
neem_shapefile_path = os.path.join(data_dir, "NEEM", "NEEMregions.shp")
reeds_mapping_hierarchy_path = os.path.join(data_dir, "mapping", "hierarchy.csv")
reeds_wind_csv_path = os.path.join(data_dir, "mapping", "gis_rs.csv")
reeds_wind_shapefile_path = os.path.join(data_dir, "rs", "rs.shp")
reeds_wind_to_ba_path = os.path.join(data_dir, "mapping", "region_map.csv")
