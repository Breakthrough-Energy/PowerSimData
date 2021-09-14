import os

import pandas as pd

from powersimdata.design.investment import const
from powersimdata.input.grid import Grid
from powersimdata.utility.distance import haversine
from powersimdata.utility.helpers import _check_import


def sjoin_nearest(left_df, right_df, search_dist=0.06):
    """Perform a spatial join between two input layers.

    :param geopandas.GeoDataFrame left_df: A dataframe of Points.
    :param geopandas.GeoDataFrame right_df: A dataframe of Polygons/Multipolygons.
    :param float/int search_dist: radius (in map units) around point to detect polygons.
    :return: (*geopandas.GeoDataFrame*) -- data frame of Points mapped to each Polygon.

    .. note:: data from nearest Polygon/Multipolygon will be used as a result if a
        Point falls outside all available Polygon/Multipolygons.
    """

    def _find_nearest(series, polygons, search_dist):
        """Find the closest polygon.

        :param pandas.Series series: point to map.
        :param geopandas.geodataframe.GeoDataFrame polygons: polygons to select from.
        :param float search_dist: radius around point to detect polygons.
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

    # Since polygons may overlap, there can be duplicated buses that we want to filter
    duplicated = points_in_regions.loc[points_in_regions.index.duplicated(keep=False)]
    to_drop = set()
    for bus in set(duplicated["bus_id"]):
        entries = duplicated.query("bus_id == @bus")
        coords = entries["geometry"].iloc[0].coords[0]  # First duped entry, only point
        regions = set(entries["name_abbr"])  # noqa: F841
        candidates = points_in_regions.query(
            "index not in @duplicated.index and name_abbr in @regions"
        )
        neighbor = candidates.apply(
            lambda x: haversine((x.geometry.x, x.geometry.y), coords), axis=1
        ).idxmin()
        closest_region = candidates.loc[neighbor, "name_abbr"]  # noqa: F841
        # There may be more than two overlapping geometries, capture all but the closest
        drop_regions = set(entries.query("name_abbr != @closest_region")["name_abbr"])
        # Since indices are duplicated, we need to drop via two-column tuples
        to_drop |= {(bus, d) for d in drop_regions}

    points_in_regions = points_in_regions.loc[
        ~points_in_regions.set_index(["bus_id", "name_abbr"]).index.isin(to_drop)
    ]

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
    """Map node to closest region.

    :param pandas.DataFrame df: data frame with node id as index and *'lat'* and
        *'lon'* as columns.
    :param str name: name of node, e.g., bus, plant, substation, etc.
    :param str shpfile: shapefile enclosing Polygon/Multipolygon with region id.
    :param float/int search_dist: radius around point to detect polygons.
    :raises ValueError: if some points are dropped because too far away from polygons.
    :return: (*geopandas.GeoDataFrame*) -- columns: id name, (point) geometry,
        region and properties of region.
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
            f"Or increase search_dist. ids dropped: {dropped}"
        )
        raise ValueError(err_msg)

    return pts_poly


def bus_to_reeds_reg(df):
    """Map bus to ReEDS regions.

    :param pandas.DataFrame df: bus data frame.
    :return: (*pandas.DataFrame*) -- index: bus id, columns rs (wind resource region)
        and rb (BA region).
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
    """Map bus to NEEM regions.

    :param pandas.DataFrame df: bus data frame.
    :return: (*pandas.DataFrame*) -- index: bus id, columns: lat, lon, name_abbr
        (NEEM region)

    .. note:: the shapefile used for mapping is pulled from the Energy Zones `Mapping
        tool <http://ezmt.anl.gov>`_. This map is overly detailed, so the shapes are
        simplified using 1 km distance (Douglas-Peucker) method in QGIS.
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


def write_bus_neem_map(base_grid):
    """Write bus location to NEEM region mapping to file.

    :param powersimdata.input.grid.Grid base_grid: a Grid instance.
    :raises TypeError: if ``base_grid`` is not a Grid instance.
    """
    if not isinstance(base_grid, Grid):
        raise TypeError("base_grid must be a Grid instance")
    df_pts_bus = bus_to_neem_reg(base_grid.bus)
    df_pts_bus.sort_index(inplace=True)
    os.makedirs(os.path.dirname(const.bus_neem_regions_path), exist_ok=True)
    df_pts_bus.to_csv(const.bus_neem_regions_path)


def write_bus_reeds_map(base_grid):
    """Write bus location to ReEDS region mapping to file.

    :param powersimdata.input.grid.Grid base_grid: a Grid instance.
    :raises TypeError: if ``base_grid`` is not a Grid instance.
    """
    if not isinstance(base_grid, Grid):
        raise TypeError("base_grid must be a Grid instance")
    df_pts_bus = bus_to_reeds_reg(base_grid.bus)
    df_pts_bus.sort_index(inplace=True)
    os.makedirs(os.path.dirname(const.bus_reeds_regions_path), exist_ok=True)
    df_pts_bus.to_csv(const.bus_reeds_regions_path)


def write_poly_shapefile():
    """Convert ReEDS wind resource csv-format file to a shapefile.

    .. note:: *gis_rs.csv* is from ReEDS open-source: */bokehpivot/in/gis_rs.csv*,
        *hierarchy.csv* is from: */bokehpivot/in/reeds2/hierarchy.csv*.
    """
    fiona = _check_import("fiona")
    shapely_geometry = _check_import("shapely.geometry")
    Polygon = shapely_geometry.Polygon  # noqa: N806
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
