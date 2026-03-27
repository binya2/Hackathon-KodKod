import math
from data_pipeline.shared.models import GeoPoint

ALT_SEPARATION = 20.0
STANDOFF_RADIUS_DEG = 0.00013  # Approx 15m in degrees

def calculate_waypoint(target_pos, index: int) -> GeoPoint:
    """Calculates a standoff waypoint around a target position."""
    angle = index * (2 * math.pi / 5)
    offset_lat = STANDOFF_RADIUS_DEG * math.cos(angle)
    offset_lon = STANDOFF_RADIUS_DEG * math.sin(angle)

    return GeoPoint(
        lat=target_pos.lat + offset_lat,
        lon=target_pos.lon + offset_lon,
        alt=150.0 + (index * ALT_SEPARATION)
    )

def calculate_distance_m(p1, p2) -> float:
    """Calculates the distance between two GeoPoints in meters."""
    return math.sqrt((p1.lat - p2.lat) ** 2 +
                       (p1.lon - p2.lon) ** 2) * 111139
