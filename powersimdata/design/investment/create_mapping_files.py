import fiona
import pandas as pd
import os
from shapely.geometry import mapping, Polygon

from powersimdata.input.grid import Grid
from powersimdata.design.investment.investment_costs import bus_to_NEEM_reg

def make_dir(filename):
    '''
    check if directory already exists where trying to write file,
    if no, create it.
    '''
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

def write_bus_NEEM_map():
    '''

    '''
    DIR = os.path.join(os.path.dirname(__file__), "Data")
    outpath = os.path.join(DIR,"buses_NEEMregion.csv")

    make_dir(outpath)

    base_grid = Grid(['USA'])

    df_pts_bus = bus_to_NEEM_reg(base_grid.bus, DIR)
    df_pts_bus.to_csv(outpath)

def write_poly_shapefile():
    '''
    Converts a ReEDS csv-format file with shapefile formatting to a shapefile
    '''
    DIR = os.path.join(os.path.dirname(__file__), "Data")
    filepath = os.path.join(DIR, "mapping/gis_rs.csv")
    outpath = os.path.join(DIR, "rs/rs.shp")

    make_dir(outpath)

    polys = pd.read_csv(filepath, sep=',', dtype={'id': object, 'group': object})
    hierarchy = pd.read_csv(os.path.join(DIR,'mapping/hierarchy.csv'))
    polys = polys.merge(hierarchy, left_on='id', right_on='rs', how='left')
    polys = polys[polys['country'] == 'usa']

    # Remove holes
    polys = polys[polys['hole'] == False].drop("hole", axis=1)

    # Define a polygon feature geometry with one attribute
    schema = {
        'geometry': 'Polygon',
        'properties': {'id': 'str'},
    }

    names = polys.group.drop_duplicates()

    # Write a new Shapefile
    with fiona.open(outpath, 'w', 'ESRI Shapefile', schema) as c:
        ## If there are multiple geometries, put the "for" loop here
        for i in names:
            poly_df = polys[polys['group'] == i]
            id_name = poly_df['id'].drop_duplicates().to_numpy()[0]

            ls = []
            for j in poly_df.index:
                ls += [(poly_df.loc[j, 'long'], poly_df.loc[j, 'lat'])]

            poly = Polygon(ls)
            c.write({
                'geometry': mapping(poly),
                'properties': {'id': id_name},
            })