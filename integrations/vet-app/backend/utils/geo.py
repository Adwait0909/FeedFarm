"""
Geographic utility functions.
Uses the Haversine formula for distance calculation.
"""

import math
from typing import Tuple


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in kilometres between two points
    on Earth using the Haversine formula.

    Args:
        lat1, lon1: Source coordinates in decimal degrees.
        lat2, lon2: Destination coordinates in decimal degrees.

    Returns:
        Distance in kilometres (float).
    """
    phi1   = math.radians(lat1)
    phi2   = math.radians(lat2)
    dphi   = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def bounding_box(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """
    Return a lat/lon bounding box for a given centre and radius.
    Used to pre-filter DB results before expensive Haversine calculation.

    Returns: (min_lat, max_lat, min_lon, max_lon)
    """
    delta_lat = radius_km / EARTH_RADIUS_KM
    delta_lon = radius_km / (EARTH_RADIUS_KM * math.cos(math.radians(lat)))

    min_lat = lat - math.degrees(delta_lat)
    max_lat = lat + math.degrees(delta_lat)
    min_lon = lon - math.degrees(delta_lon)
    max_lon = lon + math.degrees(delta_lon)

    return min_lat, max_lat, min_lon, max_lon
