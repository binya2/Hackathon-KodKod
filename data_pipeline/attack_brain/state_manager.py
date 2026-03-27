import logging
from typing import List, Optional

from data_pipeline.shared.models import DroneTelemetry, TargetTelemetry
from data_pipeline.shared.redis_utils import redis_client

logger = logging.getLogger(__name__)


async def get_target(target_id: str) -> Optional[TargetTelemetry]:
    """Retrieves a target from Redis by its ID."""
    res = await redis_client.hget("targets", target_id)
    if res:
        try:
            return TargetTelemetry.model_validate_json(res)
        except Exception:
            return None
    return None


async def get_active_targets() -> List[TargetTelemetry]:
    """Returns all targets with health > 0 from Redis, excluding TGT-INIT."""
    targets_raw = await redis_client.hgetall("targets")
    targets = []
    for v in targets_raw.values():
        try:
            t = TargetTelemetry.model_validate_json(v)
            if t.health > 0 and t.target_id != "TGT-INIT":
                targets.append(t)
        except Exception:
            pass
    return targets


async def update_drone_telemetry(telemetry: DroneTelemetry):
    """Updates Redis with new drone telemetry."""
    await redis_client.hset("drones", telemetry.drone_id, telemetry.model_dump_json())


async def get_active_attack_drones() -> List[DroneTelemetry]:
    """Returns a list of all active attack drones from Redis."""
    drones_raw = await redis_client.hgetall("drones")
    active_attack = []
    for v in drones_raw.values():
        try:
            d = DroneTelemetry.model_validate_json(v)
            if d.role.lower() == "attack" and d.flight_status in ["ACTIVE", "ATTACKING", "EN_ROUTE"]:
                active_attack.append(d)
        except Exception:
            pass
    return active_attack


async def get_sleeping_attack_drones() -> List[DroneTelemetry]:
    """Returns a list of all sleeping attack drones from Redis."""
    drones_raw = await redis_client.hgetall("drones")
    sleeping_attack = []
    for v in drones_raw.values():
        try:
            d = DroneTelemetry.model_validate_json(v)
            if d.role.lower() == "attack" and d.flight_status == "SLEEP":
                sleeping_attack.append(d)
        except Exception:
            pass
    return sleeping_attack


async def get_drones_on_target(target_id: str) -> List[DroneTelemetry]:
    """Returns a list of active attack drones assigned to a specific target."""
    active_attack = await get_active_attack_drones()
    return [d for d in active_attack if d.assigned_target_id == target_id]
