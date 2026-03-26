import logging
import os
import redis.asyncio as redis
from datetime import datetime, timezone
from data_pipeline.shared_models import WorldState, DroneTelemetry, TargetTelemetry

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)


async def update_drone_telemetry(telemetry: DroneTelemetry):
    """Updates Redis with new drone telemetry."""
    await redis_client.hset("drones", telemetry.drone_id, telemetry.model_dump_json())


async def update_target_telemetry(telemetry: TargetTelemetry):
    """Updates Redis with new target telemetry."""
    await redis_client.hset("targets", telemetry.target_id, telemetry.model_dump_json())


async def garbage_collect_stale_drones():
    """Removes drones from Redis that have not sent telemetry for a while."""
    now = datetime.now(timezone.utc)
    drones_raw = await redis_client.hgetall("drones")

    for drone_id, drone_json in drones_raw.items():
        try:
            drone = DroneTelemetry.model_validate_json(drone_json)
            if (now - drone.timestamp).total_seconds() > 15.0:
                logger.warning(f"Removing stale drone %s from state (no telemetry for >15s)", drone_id)
                await redis_client.hdel("drones", drone_id)
        except Exception as e:
            logger.error(f"Error parsing drone {drone_id}: {e}")
            await redis_client.hdel("drones", drone_id)


async def garbage_collect_dead_targets():
    """Removes dead targets from Redis after 30 seconds."""
    now = datetime.now(timezone.utc)
    targets_raw = await redis_client.hgetall("targets")

    for target_id, target_json in targets_raw.items():
        try:
            target = TargetTelemetry.model_validate_json(target_json)
            if target.health <= 0 and (now - target.timestamp).total_seconds() > 30.0:
                logger.info(f"Removing dead target %s from state (dead for >30s)", target_id)
                await redis_client.hdel("targets", target_id)
        except Exception as e:
            logger.error(f"Error parsing target {target_id}: {e}")


async def get_world_state() -> WorldState:
    """Constructs and returns the current world state from Redis."""
    await garbage_collect_stale_drones()
    await garbage_collect_dead_targets()

    drones_raw = await redis_client.hgetall("drones")
    targets_raw = await redis_client.hgetall("targets")

    drones = []
    for v in drones_raw.values():
        try:
            drones.append(DroneTelemetry.model_validate_json(v))
        except Exception as e:
            logger.error(f"Error parsing drone telemetry: {e}")

    targets = []
    for v in targets_raw.values():
        try:
            targets.append(TargetTelemetry.model_validate_json(v))
        except Exception as e:
            logger.error(f"Error parsing target telemetry: {e}")

    world_state = WorldState()
    world_state.timestamp = datetime.now(timezone.utc)

    # Use lowercase comparison for robustness
    world_state.recon_data = sorted(
        [d for d in drones if d.role.lower() == "recon"],
        key=lambda x: 0 if x.flight_status == "ACTIVE" else 1
    )

    world_state.attack_data = sorted(
        [d for d in drones if d.role.lower() == "attack"],
        key=lambda x: 0 if x.flight_status == "ACTIVE" else 1
    )

    world_state.target_data = [t for t in targets if t.health > 0]

    return world_state
