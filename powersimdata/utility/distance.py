from math import radians, cos, sin, asin, sqrt

import geopy.distance


def haversine(point1, point2):
    """Given two lat/long pairs, return distance in miles.

    :param tuple point1: first point, (lat, long) in degrees.
    :param tuple point2: second point, (lat, long) in degrees.
    :return: (*float*) -- distance in miles.
    """

    _AVG_EARTH_RADIUS_MILES = 3958.7613

    # unpack latitude/longitude
    lat1, lng1 = point1
    lat2, lng2 = point2

    # convert all latitudes/longitudes from decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))

    # calculate haversine
    lat = lat2 - lat1
    lng = lng2 - lng1
    d = 2 * _AVG_EARTH_RADIUS_MILES * asin(sqrt(
        sin(lat * 0.5) ** 2 + cos(lat1) * cos(lat2) * sin(lng * 0.5) ** 2))

    return d


def great_circle_distance(x):
    """Calculates distance between two sites.

    :param pandas.dataFrame x: start and end point coordinates of branches.
    :return: (*float*) -- length of branch (in km.).
    """
    site_coords = (x.from_lat, x.from_lon)
    place2_coords = (x.to_lat, x.to_lon)
    return geopy.distance.vincenty(site_coords, place2_coords).km
