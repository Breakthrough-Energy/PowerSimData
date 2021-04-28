from math import acos, asin, cos, degrees, radians, sin, sqrt


def haversine(point1, point2):
    """Given two lat/long pairs, return distance in miles.

    :param tuple point1: first point, (lat, long) in degrees.
    :param tuple point2: second point, (lat, long) in degrees.
    :return: (*float*) -- distance in miles.
    """

    _AVG_EARTH_RADIUS_MILES = 3958.7613  # noqa: N806

    # unpack latitude/longitude
    lat1, lng1 = point1
    lat2, lng2 = point2

    # convert all latitudes/longitudes from decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))

    # calculate haversine
    lat = lat2 - lat1
    lng = lng2 - lng1
    d = (
        2
        * _AVG_EARTH_RADIUS_MILES
        * asin(sqrt(sin(lat * 0.5) ** 2 + cos(lat1) * cos(lat2) * sin(lng * 0.5) ** 2))
    )

    return d


def great_circle_distance(x):
    """Calculates distance between two sites.

    :param pandas.dataFrame x: start and end point coordinates of branches.
    :return: (*float*) -- length of branch (in km.).
    """
    mi_to_km = 1.60934
    return haversine((x.from_lat, x.from_lon), (x.to_lat, x.to_lon)) * mi_to_km


def ll2uv(lon, lat):
    """Convert (longitude, latitude) to unit vector.

    :param float lon: longitude of the site (in deg.) measured eastward from
        Greenwich, UK.
    :param float lat: latitude of the site (in deg.). Equator is the zero point.
    :return: (*list*) -- 3-components (x,y,z) unit vector.
    """
    cos_lat = cos(radians(lat))
    sin_lat = sin(radians(lat))
    cos_lon = cos(radians(lon))
    sin_lon = sin(radians(lon))

    uv = [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat]

    return uv


def angular_distance(uv1, uv2):
    """Calculate the angular distance between two vectors.

    :param list uv1: 3-components vector as returned by :func:`ll2uv`.
    :param list uv2: 3-components vector as returned by :func:`ll2uv`.
    :return: (*float*) -- angle (in degrees).
    """
    cos_angle = uv1[0] * uv2[0] + uv1[1] * uv2[1] + uv1[2] * uv2[2]
    if cos_angle >= 1:
        cos_angle = 1
    if cos_angle <= -1:
        cos_angle = -1
    angle = degrees(acos(cos_angle))

    return angle


def find_closest_neighbor(point, neighbors):
    """Locates the closest neighbor.

    :param tuple point: (lon, lat) in degrees.
    :param list neighbors: each element of the list are the (lon, lat)
        of potential neighbor.
    :return: (*int*) -- id of the closest neighbor
    """
    uv_point = ll2uv(point[0], point[1])
    id_neighbor = None
    angle_min = float("inf")
    for i, n in enumerate(neighbors):
        angle = angular_distance(uv_point, ll2uv(n[0], n[1]))
        if angle < angle_min:
            id_neighbor = i
            angle_min = angle

    return id_neighbor
