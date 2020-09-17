import fiona
import pandas as pd
import os
import errno
from shapely.geometry import mapping, Polygon
import geopandas as gpd
#import osmnx as ox

from powersimdata.input.grid import Grid

def sjoin_nearest(left_df, right_df, search_dist=0.06, report_dist=False,
                  lsuffix='left', rsuffix='right'):
    """
    Perform a spatial join between two input layers.
    If a geometry in left_df falls outside (all) geometries in right_df, the data from nearest Polygon will be used as a result.
    To make queries faster, change "search_dist."
    :param geopandas.GeoDataFrame left_df: A dataframe of Points.
    :param geopandas.GeoDataFrame right_df: A dataframe of Polygons/Multipolygons
    :param float/int search_dist: parameter (specified in map units) can be used to limit the search area for geometries around source points. Can make query faster.
    :param boolean report_dist: if True, the distance for closest geometry will be reported in a column called `dist`. If geometries intersect, the distance will be 0.
    :return: *geopandas.GeoDataFrame* result -- A dataframe of Points mapped to each polygon in right_df.
    """

    # Explode possible MultiGeometries
    right_df = right_df.explode()
    right_df = right_df.reset_index(drop=True)

    if 'index_left' in left_df.columns:
        left_df = left_df.drop('index_left', axis=1)

    if 'index_right' in left_df.columns:
        left_df = left_df.drop('index_right', axis=1)

    if report_dist:
        if 'dist' in left_df.columns:
            raise ValueError("'dist' column exists in the left DataFrame. Remove it, or set 'report_dist' to False.")

    # Get geometries that intersect or do not intersect polygons
    mask = left_df.intersects(right_df.unary_union)
    geoms_intersecting_polygons = left_df.loc[mask]
    geoms_outside_polygons = left_df.loc[~mask]

    # Make spatial join between points that fall inside the Polygons
    if geoms_intersecting_polygons.shape[0] > 0:
        pip_join = gpd.sjoin(left_df=geoms_intersecting_polygons, right_df=right_df, op='intersects')

        if report_dist:
            pip_join['dist'] = 0

    else:
        pip_join = gpd.GeoDataFrame()

    # Get nearest geometries
    closest_geometries = gpd.GeoDataFrame()

    # A tiny snap distance buffer is needed in some cases
    snap_dist = 0.00000005

    # Closest points from source-points to polygons
    for idx, geom in geoms_outside_polygons.iterrows():
        # Get geometries within search distance
        candidates = right_df.loc[right_df.intersects(geom[left_df.geometry.name].buffer(search_dist))]

        if len(candidates) == 0:
            continue
        unary = candidates.unary_union

        if unary.geom_type == 'Polygon':

            # Get exterior of the Polygon
            exterior = unary.exterior

            # Find a point from Polygons that is closest to the source point
            closest_geom = exterior.interpolate(exterior.project(geom[left_df.geometry.name]))

            if report_dist:
                distance = closest_geom.distance(geom[left_df.geometry.name])

            # Select the Polygon
            closest_poly = right_df.loc[right_df.intersects(closest_geom.buffer(snap_dist))]

        elif unary.geom_type == 'MultiPolygon':
            # Keep track of distance for closest polygon
            distance = 9999999999
            closest_geom = None

            for idx, poly in enumerate(unary):
                # Get exterior of the Polygon
                exterior = poly.exterior

                # Find a point from Polygons that is closest to the source point
                closest_candidate = exterior.interpolate(exterior.project(geom[left_df.geometry.name]))

                # Calculate distance between origin point and the closest point in Polygon
                dist = geom[left_df.geometry.name].distance(closest_candidate)

                # If the point is closer to given polygon update the info
                if dist < distance:
                    distance = dist
                    closest_geom = closest_candidate

            # Select the Polygon that was closest
            closest_poly = right_df.loc[right_df.intersects(closest_geom.buffer(snap_dist))]
        else:
            print("Incorrect input geometry type. Skipping ..")

        # Reset index
        geom = geom.to_frame().T.reset_index(drop=True)

        # Drop geometry from closest polygon
        closest_poly = closest_poly.drop(right_df.geometry.name, axis=1)
        closest_poly = closest_poly.reset_index(drop=True)

        # Join values
        join = geom.join(closest_poly, lsuffix='_%s' % lsuffix, rsuffix='_%s' % rsuffix)

        # Add information about distance to closest geometry if requested
        if report_dist:
            if 'dist' in join.columns:
                raise ValueError("'dist' column exists in the DataFrame. Remove it, or set 'report_dist' to False.")
            join['dist'] = distance

        closest_geometries = closest_geometries.append(join, ignore_index=True, sort=False)

    # Merge everything together
    result = pip_join.append(closest_geometries, ignore_index=True, sort=False)
    return result


def make_dir(filename):
    '''
    Check if directory already exists where trying to write file, if no, create it.
    :param str filename: filename to create base directory for.
    '''
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

def points_to_polys(df, name, DIR, shpfile, crs="EPSG:4326",search_dist=0.04):
    '''Given a dataframe of lat/lon's, and a shapefile of Polygons/Multipolygon regions, map df.index to closest regions.

    :param pandas.DataFrame df: grid.plant instance.
    :param str name: what to name the id (bus or plant here)
    :param str DIR: Data directory
    :param str shpfile: name of shapefile containing a collection Polygon/Multipolygon shapes with region IDs.
    :param str crs: coordinate reference system
    :param float/int search_dist: distance to search from point for nearest polygon.
    :return: (*geopandas.GeoDataFrame*) --  columns: index id, (point) geometry, [region, other properties of region]
    '''
    polys = gpd.read_file(os.path.join(DIR, shpfile))

    # If no assigned crs, assign it. If it has another crs assigned, convert it.
    if polys.crs == None:
        polys.crs = crs
    elif polys.crs != crs:
        polys = polys.to_crs(crs)

    # load buses into Points geodataframe
    pts = gpd.GeoDataFrame(pd.DataFrame({name + '_id': df.index}),
                           geometry=gpd.points_from_xy(df.lon, df.lat), crs=crs)

    # find which ReEDS region the points belong to
    # (within the region or as close as possible, if in the ocean or something)
    pts_poly = sjoin_nearest(left_df=pts, right_df=polys, search_dist=search_dist)
    pts_poly = pts_poly.drop("index_right", axis=1)
    return pts_poly

def plant_to_ReEDS_reg(df, DIR):
    """Given a dataframe of plants, return a dataframe of plant_id's with associated ReEDS regions (wind resource regions (rs) and BA regions (rb)).
    Used to map regional generation investment cost multipliers.
    region_map.csv is from: "/bokehpivot/in/reeds2/region_map.csv".
    rs/rs.shp is created with write_poly_shapefile().

    :param pandas.DataFrame df: grid.plant instance.
    :param str DIR: Data directory
    :return: (*pandas.DataFrame*) -- plant_id map. columns: plant_id, rs, rb
    """
    # load polygons for ReEDS BAs
    # warning that these polygons are rough and not very detailed - meant for illustrative purposes. Might be worth it later to revisit and try to fine-tune this
    # but since the multipliers aren't super strict by region, it's fine for now.

    pts_poly = points_to_polys(df, "plant", DIR, shpfile='rs/rs.shp', search_dist=0.2)

    # load in rs to rb region mapping file
    region_map = pd.read_csv(os.path.join(DIR, 'mapping/region_map.csv'))

    # map rs (wind region) to rb (ba region)
    pts_poly = pts_poly.merge(region_map, left_on='id', right_on='rs', how='left')
    pts_poly = pd.DataFrame(pts_poly).drop(["geometry","id"], axis=1)

    return pts_poly

def bus_to_NEEM_reg(df, DIR):
    """Given a dataframe of buses, return a dataframe of bus_id's with associated NEEM region, lat, and lon of bus.
    Used to map regional transmission investment cost multipliers.
    Shapefile used to map is 'NEEM/NEEMregions.shp' which is pulled from Energy Zones Mapping Tool at http://ezmt.anl.gov. This map is overly \
    detailed, so I simplified the shapes using 1 km distance (Douglas-Peucker) method in QGIS.


    :param pandas.DataFrame df: grid.bus instance.
    :param str DIR: Data directory
    :return: (*pandas.DataFrame*) -- bus_id map. columns: bus_id, lat, lon, name_abbr (NEEM region)

    Note: mapping may take a while, especially for many points.
    """

    pts_poly = points_to_polys(df, "bus", DIR, shpfile='NEEM/NEEMregions.shp')

    #save lat/lon for consistency check later in _calculate_ac_inv_costs
    pts_poly["lon"] = pts_poly.geometry.x
    pts_poly["lat"] = pts_poly.geometry.y

    pts_poly = pd.DataFrame(pts_poly).drop(["geometry","name", "shape_area", "shape_leng"],
                                           axis=1)
    return pts_poly


def write_bus_NEEM_map():
    '''
    Maps the bus locations from the base USA grid to NEEM regions.
    Writes out csv with bus numbers, associated NEEM region, and lat/lon of bus (to check if consistent with bus location in _calculate_ac_inv_costs).
    Shapefile used to map is 'NEEM/NEEMregions.shp' which is pulled from Energy Zones Mapping Tool at http://ezmt.anl.gov. This map is overly \
    detailed, so I simplified the shapes using 1 km distance (Douglas-Peucker) method in QGIS.

    Note: This code takes a few hours to run. Should only need to run once for all buses. If there are only a few changed buses, the regional \
    multiplier code can handle it.
    '''
    DIR = os.path.join(os.path.dirname(__file__), "Data")
    outpath = os.path.join(DIR,"buses_NEEMregion.csv")

    make_dir(outpath)

    base_grid = Grid(['USA'])
    df_pts_bus = bus_to_NEEM_reg(base_grid.bus, DIR)
    df_pts_bus.to_csv(outpath)

def write_poly_shapefile():
    '''
    Converts a ReEDS csv-format file to a shapefile. Shouldn't need to run again unless new source data.
    Right now, hard-coded read ReEDS wind resource regions (labelled rs).
    gis_rs.csv is from ReEDS open-source: "/bokehpivot/in/gis_rs.csv"
    hierarchy.csv is from: "/bokehpivot/in/reeds2/hierarchy.csv"
    writes out the shapefile in "rs/rs.shp"

    Note: These ReEDS wind resource region shapes are approximate. Thus, there are probably some mistakes, but this is \
    currently only used for mapping plant regional multipliers, which are approximate anyway, so it should be fine.
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