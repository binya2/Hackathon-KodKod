import logging
from typing import List

from data_pipeline.shared.models import DroneTelemetry, TargetTelemetry
from data_pipeline.shared.redis_utils import redis_client

logger = logging.getLogger(__name__)


async def update_drone_telemetry(telemetry: DroneTelemetry):
    """Updates Redis with new drone telemetry."""
    await redis_client.hset("drones", telemetry.drone_id, telemetry.model_dump_json())


async def get_active_recon_drones() -> List[DroneTelemetry]:
    """Returns a list of active recon drones from Redis."""
    drones_raw = await redis_client.hgetall("drones")
    active = []
    for v in drones_raw.values():
        try:
            d = DroneTelemetry.model_validate_json(v)
            if d.role.lower() == "recon" and d.flight_status in ["ACTIVE", "EN_ROUTE"]:
                active.append(d)
        except Exception:
            pass
    return active


async def get_sleeping_recon_drones() -> List[DroneTelemetry]:
    """Returns a list of sleeping recon drones from Redis."""
    drones_raw = await redis_client.hgetall("drones")
    sleeping = []
    for v in drones_raw.values():
        try:
            d = DroneTelemetry.model_validate_json(v)
            if d.role.lower() == "recon" and d.flight_status == "SLEEP":
                sleeping.append(d)
        except Exception:
            pass
    return sleeping


async def get_active_recon_drone_for_target(target_id: str) -> List[DroneTelemetry]:
    """Returns a list of recon drones assigned to a specific target, excluding SLEEP or RETURNING."""
    drones_raw = await redis_client.hgetall("drones")
    matching = []
    for v in drones_raw.values():
        try:
            d = DroneTelemetry.model_validate_json(v)
            if (d.role.lower() == "recon" and
                    d.assigned_target_id == target_id and
                    d.flight_status not in ["SLEEP", "RETURNING"]):
                matching.append(d)
        except Exception:
            pass
    return matching
