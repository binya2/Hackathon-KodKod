import logging
import os
import redis.asyncio as redis
from typing import List
from data_pipeline.shared_models import DroneTelemetry, TargetTelemetry

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)


async def update_target(target: TargetTelemetry):
    """Adds or updates a target in Redis."""
    await redis_client.hset("targets", target.target_id, target.model_dump_json())


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
            if d.role.lower() == "recon" and d.flight_status == "ACTIVE":
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
    """Returns a list of active recon drones assigned to a specific target."""
    active = await get_active_recon_drones()
    return [d for d in active if d.assigned_target_id == target_id]
