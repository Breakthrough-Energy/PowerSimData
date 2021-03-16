from math import sqrt

from numpy.testing import assert_almost_equal, assert_array_almost_equal

from powersimdata.utility.distance import angular_distance, find_closest_neighbor, ll2uv


def test_ll2uv():
    assert_array_almost_equal(ll2uv(0, 0), [1.0, 0.0, 0.0])
    assert_array_almost_equal(ll2uv(0, 90), [0.0, 0.0, 1.0])  # north pole
    assert_array_almost_equal(ll2uv(45, 90), [0.0, 0.0, 1.0])  # north pole
    assert_array_almost_equal(ll2uv(90, 90), [0.0, 0.0, 1.0])  # north pole
    assert_array_almost_equal(ll2uv(-45, -90), [0.0, 0.0, -1.0])  # south pole
    assert_array_almost_equal(ll2uv(-90, -90), [0.0, 0.0, -1.0])  # south pole
    assert_array_almost_equal(ll2uv(-120, -90), [0.0, 0, -1.0])  # south pole
    assert_array_almost_equal(ll2uv(45, 45), [1 / 2, 1 / 2, sqrt(2) / 2])
    assert_array_almost_equal(ll2uv(60, 60), [1 / 4, sqrt(3) / 4, sqrt(3) / 2])


def test_angular_distance():
    # pole to pole
    assert_almost_equal(angular_distance([0.0, 0, 1.0], [0.0, 0, -1.0]), 180)
    # equator to north pole
    assert_almost_equal(angular_distance([1.0, 0, 0.0], [0.0, 0, 1.0]), 90)
    # equator to south pole
    assert_almost_equal(
        angular_distance([sqrt(2) / 2, sqrt(2) / 2, 0.0], [0.0, 0, -1.0]), 90
    )
    # 45 deg longitude to 60 deg longitude
    assert_almost_equal(
        angular_distance([sqrt(2) / 2, sqrt(2) / 2, 0.0], [1 / 2, sqrt(3) / 2, 0.0]), 15
    )


def test_find_closest_neighbor():
    point = (45, 45)
    neighbors = [
        [0, 45],
        [10, 50],
        [40, 40],
        [-120, -60],
        [44.75, 45.1],
        [-270, 5],
        [43, 46],
        [320, 45],
        [45, 44],
        [44, 45],
        [44.5, 45.5],
    ]
    closest_neighbor_id = find_closest_neighbor(point, neighbors)
    assert closest_neighbor_id == 4
