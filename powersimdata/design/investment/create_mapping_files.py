import os

import pandas as pd

from powersimdata.design.investment import const
from powersimdata.input.grid import Grid
from powersimdata.utility.helpers import _check_import


def sjoin_nearest(left_df, right_df, search_dist=0.06):
    """
    Perform a spatial join between two input layers.
    If a geometry in left_df falls outside (all) geometries in right_df, the data from
        nearest Polygon will be used as a result.
    To make queries faster, change "search_dist."
    :param geopandas.GeoDataFrame left_df: A dataframe of Points.
    :param geopandas.GeoDataFrame right_df: A dataframe of Polygons/Multipolygons
    :param float/int search_dist: parameter (specified in map units) is used to limit
        the search area for geometries around source points. Smaller -> faster runtime.
    :return: (*geopandas.GeoDataFrame*) -- A dataframe of Points mapped to each polygon
        in right_df.
    """

    def _find_nearest(series, polygons, search_dist):
        """Given a row with a bus id and a Point, find the closest polygon.

        :param pandas.Series series: point to map.
        :param geopandas.geodataframe.GeoDataFrame polygons: polygons to select from.
        :param float search_dist: radius around point to detect polygons in.
        """
        geom = series[left_df.geometry.name]
        # Get geometries within search distance
        candidates = polygons.loc[polygons.intersects(geom.buffer(search_dist))]

        if len(candidates) == 0:
            raise ValueError(f"No polygons found within {search_dist} of {series.name}")

        # Select the closest Polygon
        distances = candidates.apply(
            lambda x: geom.distance(x[candidates.geometry.name].exterior), axis=1
        )
        closest_poly = polygons.loc[distances.idxmin].to_frame().T

        # Reset index
        series = series.to_frame().T.reset_index(drop=True)

        # Drop geometry from closest polygon
        closest_poly = closest_poly.drop(polygons.geometry.name, axis=1)
        closest_poly = closest_poly.reset_index(drop=True)

        # Join values
        join = series.join(closest_poly, lsuffix="_left", rsuffix="_right")

        # Add information about distance to closest geometry if requested
        join["dist"] = distances.min()

        return join.squeeze()

    gpd = _check_import("geopandas")

    if "dist" in (set(left_df.columns) | set(right_df.columns)):
        raise ValueError("neither series nor polygons can contain a 'dist' column")

    # Explode possible MultiGeometries. This is a major speedup!
    right_df = right_df.explode()
    right_df = right_df.reset_index(drop=True)

    # Make spatial join between points that fall inside the Polygons
    points_in_regions = gpd.sjoin(left_df=left_df, right_df=right_df, op="intersects")
    points_in_regions["dist"] = 0

    # Find closest Polygons, for points that don't fall within any
    missing_indices = set(left_df.index) - set(points_in_regions.index)
    points_not_in_regions = left_df.loc[missing_indices]
    closest_geometries = points_not_in_regions.apply(
        _find_nearest, args=(right_df, search_dist), axis=1
    )

    # Merge everything together
    closest_geometries = gpd.GeoDataFrame(closest_geometries)
    result = points_in_regions.append(closest_geometries, ignore_index=True, sort=False)
    return result


def points_to_polys(df, name, shpfile, search_dist=0.04):
    """Given a dataframe which includes 'lat' and 'lon' columns, and a shapefile of
        Polygons/Multipolygon regions, map df.index to closest regions.

    :param pandas.DataFrame df: includes an index, and 'lat' and 'lon' columns.
    :param str name: what to name the id (bus, plant, substation, etc)
    :param str shpfile: name of shapefile containing a collection Polygon/Multipolygon
        shapes with region IDs.
    :param float/int search_dist: distance to search from point for nearest polygon.
    :raises ValueError: if some points are dropped because too far away from polys.
    :return: (*geopandas.GeoDataFrame*) --
        columns: index id, (point) geometry, [region, other properties of region]
    """
    gpd = _check_import("geopandas")
    polys = gpd.read_file(shpfile)

    # If no assigned crs, assign it. If it has another crs assigned, convert it.
    crs = "EPSG:4326"
    if polys.crs is None:
        polys.crs = crs
    elif polys.crs != crs:
        polys = polys.to_crs(crs)

    # load buses into Points geodataframe
    id_name = name + "_id"
    pts = gpd.GeoDataFrame(
        pd.DataFrame({id_name: df.index}),
        geometry=gpd.points_from_xy(df.lon, df.lat),
        crs=crs,
    )

    # find which ReEDS region the points belong to
    # (within the region or as close as possible, if in the ocean or something)
    pts_poly = sjoin_nearest(left_df=pts, right_df=polys, search_dist=search_dist)
    pts_poly = pts_poly.drop("index_right", axis=1)

    if len(pts) > len(pts_poly):
        dropped = pts[~pts[id_name].isin(pts_poly[id_name])][id_name].to_list()
        err_msg = (
            "Some points dropped because could not be mapped to regions. "
            "Check your lat/lon values to be sure it's in the US. "
            f"Or increase search_dist if close. Problem ids: {dropped}"
        )
        raise ValueError(err_msg)

    return pts_poly


def bus_to_reeds_reg(df):
    """Given a dataframe of buses, return a dataframe of bus_id's with associated
        ReEDS regions (wind resource regions (rs) and BA regions (rb)).
    Used to map regional generation investment cost multipliers.
    region_map.csv is from: "/bokehpivot/in/reeds2/region_map.csv".
    rs/rs.shp is created with :py:func:`write_poly_shapefile`.

    :param pandas.DataFrame df: grid bus dataframe.
    :return: (*pandas.DataFrame*) -- bus_id map. columns: bus_id, rs, rb
    """
    pts_poly = points_to_polys(
        df, "bus", const.reeds_wind_shapefile_path, search_dist=2
    )

    # load in rs to rb region mapping file
    region_map = pd.read_csv(const.reeds_wind_to_ba_path)

    # map rs (wind region) to rb (ba region)
    pts_poly = pts_poly.merge(region_map, left_on="id", right_on="rs", how="left")
    pts_poly = pd.DataFrame(pts_poly).drop(["geometry", "id"], axis=1)
    pts_poly.set_index("bus_id", inplace=True)

    return pts_poly


def bus_to_neem_reg(df):
    """Given a dataframe of buses, return a dataframe of bus_id's with associated
        NEEM region, lat, and lon of bus.
    Used to map regional transmission investment cost multipliers.
    Shapefile used to map is 'data/NEEM/NEEMregions.shp' which is pulled from Energy
        Zones `Mapping tool <http://ezmt.anl.gov>`_. This map is overly detailed, so I
        simplified the shapes using 1 km distance (Douglas-Peucker) method in QGIS.

    :param pandas.DataFrame df: grid.bus instance.
    :return: (*pandas.DataFrame*) -- bus_id map.
        columns: bus_id, lat, lon, name_abbr (NEEM region)

    Note: mapping may take a while, especially for many points.
    """

    pts_poly = points_to_polys(df, "bus", const.neem_shapefile_path, search_dist=1)

    # save lat/lon for consistency check later in _calculate_ac_inv_costs
    pts_poly["lat"] = pts_poly.geometry.y
    pts_poly["lon"] = pts_poly.geometry.x

    pts_poly = pd.DataFrame(pts_poly).drop(
        ["geometry", "name", "shape_area", "shape_leng"], axis=1
    )
    pts_poly.set_index("bus_id", inplace=True)
    return pts_poly


def write_bus_neem_map():
    """
    Maps the bus locations from the base USA grid to NEEM regions.
    Writes out csv with bus numbers, associated NEEM region, and lat/lon of bus
        (to check if consistent with bus location in _calculate_ac_inv_costs).
    """
    base_grid = Grid(["USA"])
    df_pts_bus = bus_to_neem_reg(base_grid.bus)
    df_pts_bus.sort_index(inplace=True)
    os.makedirs(const.bus_neem_regions_path, exist_ok=True)
    df_pts_bus.to_csv(const.bus_neem_regions_path)


def write_bus_reeds_map():
    """
    Maps the bus locations from the base USA grid to ReEDS regions.
    Writes out csv with bus numbers, associated ReEDS regions, and distances.
    """
    base_grid = Grid(["USA"])
    df_pts_bus = bus_to_reeds_reg(base_grid.bus)
    df_pts_bus.sort_index(inplace=True)
    os.makedirs(const.bus_reeds_regions_path, exist_ok=True)
    df_pts_bus.to_csv(const.bus_reeds_regions_path)


def write_poly_shapefile():
    """
    Converts a ReEDS csv-format file to a shapefile. Shouldn't need to run again
        unless new source data.
    Right now, hard-coded read ReEDS wind resource regions (labelled rs).
    gis_rs.csv is from ReEDS open-source: "/bokehpivot/in/gis_rs.csv"
    hierarchy.csv is from: "/bokehpivot/in/reeds2/hierarchy.csv"
    writes out the shapefile in "rs/rs.shp"

    Note: These ReEDS wind resource region shapes are approximate. Thus, there are
        probably some mistakes, but this is currently only used for mapping plant
        regional multipliers, which are approximate anyway, so it should be fine.
    """
    fiona = _check_import("fiona")
    shapely_geometry = _check_import("shapely.geometry")
    Polygon = shapely_geometry.Polygon
    mapping = shapely_geometry.mapping

    outpath = const.reeds_wind_shapefile_path
    os.makedirs(outpath, exist_ok=True)

    polys = pd.read_csv(
        const.reeds_wind_csv_path, sep=",", dtype={"id": object, "group": object}
    )
    hierarchy = pd.read_csv(const.reeds_mapping_hierarchy_path)
    polys = polys.merge(hierarchy, left_on="id", right_on="rs", how="left")
    polys = polys[polys["country"] == "usa"]

    # Remove holes
    polys = polys[polys["hole"] == False].drop("hole", axis=1)  # noqa: E712

    # Define a polygon feature geometry with one attribute
    schema = {
        "geometry": "Polygon",
        "properties": {"id": "str"},
    }

    names = polys.group.drop_duplicates()

    # Write a new Shapefile
    with fiona.open(outpath, "w", "ESRI Shapefile", schema) as c:
        # If there are multiple geometries, put the "for" loop here
        for i in names:
            poly_df = polys[polys["group"] == i]
            id_name = poly_df["id"].drop_duplicates().to_numpy()[0]

            ls = []
            for j in poly_df.index:
                ls += [(poly_df.loc[j, "long"], poly_df.loc[j, "lat"])]

            poly = Polygon(ls)
            c.write(
                {
                    "geometry": mapping(poly),
                    "properties": {"id": id_name},
                }
            )
