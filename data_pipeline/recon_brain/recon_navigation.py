import math
from data_pipeline.shared.models import GeoPoint

RECON_ALTITUDE_OFFSET = 200.0

def calculate_recon_waypoint(target_pos, index: int) -> GeoPoint:
    """Calculates a standoff waypoint for a recon drone."""
    return GeoPoint(
        lat=target_pos.lat + 0.00005,
        lon=target_pos.lon + 0.00005,
        alt=RECON_ALTITUDE_OFFSET + (index * 10.0)
    )

def calculate_distance_m(p1, p2) -> float:
    """Calculates the distance between two points in meters."""
    return math.sqrt((p1.lat - p2.lat) ** 2 +
                       (p1.lon - p2.lon) ** 2) * 111139
