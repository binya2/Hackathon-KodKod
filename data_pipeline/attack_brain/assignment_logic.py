import asyncio
import json
import logging
import math
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer

from data_pipeline.attack_brain.state_manager import (
    get_active_attack_drones,
    get_target,
    get_active_targets,
    get_drones_on_target,
    update_drone_telemetry,
)
from data_pipeline.shared_models import GeoPoint, DroneCommand

logger = logging.getLogger(__name__)

ALT_SEPARATION = 20.0
STANDOFF_RADIUS_DEG = 0.00013  # Approx 15m in degrees


async def assignment_loop(producer: AIOKafkaProducer):
    """Continuously evaluates drone positions relative to their assigned targets."""
    while True:
        all_drones = await get_active_attack_drones()
        active_targets = await get_active_targets()

        for target in active_targets:
            if target.target_id == "TGT-INIT":
                continue
            assigned_count = sum(
                1 for d in all_drones
                if d.assigned_target_id == target.target_id and d.flight_status in ["ACTIVE", "ATTACKING", "EN_ROUTE"]
            )
            if assigned_count < 2:
                logger.info(
                    f"[ASSIGN] Target {target.target_id} has {assigned_count} drones. Requesting replacement...")
                await _request_replacement(target, producer)

        for drone in all_drones:
            if drone.flight_status == "MANUAL":
                continue
            if not drone.assigned_target_id or drone.flight_status in ["RETURNING", "SLEEP"]:
                continue
            await _process_drone_assignment(drone, producer, all_drones, active_targets)

        await asyncio.sleep(1.0)


async def _process_drone_assignment(drone, producer: AIOKafkaProducer, all_drones, active_targets):
    target = await get_target(drone.assigned_target_id)

    if not target or target.health <= 0:
        new_target = next(
            (t for t in active_targets if sum(1 for d in all_drones if d.assigned_target_id == t.target_id) < 2), None)
        if new_target:
            logger.info(
                f"[RE-ASSIGN] Drone {drone.drone_id} moved from dead {drone.assigned_target_id} to {new_target.target_id}")
            drone.assigned_target_id = new_target.target_id
            await update_drone_telemetry(drone)
            target = new_target
        else:
            await _recall_drone(drone.drone_id, producer)
            return

    if drone.flight_status == "ATTACKING":
        return

    if drone.role == "attack" and drone.weapons_count == 0:
        replacement_sent = any(
            d.assigned_target_id == drone.assigned_target_id and d.drone_id != drone.drone_id for d in all_drones)
        if not replacement_sent:
            logger.info(
                f"[AMMO] Drone {drone.drone_id} out of ammo. Requesting replacement for {drone.assigned_target_id}...")
            await _request_replacement(target, producer)

        logger.info(f"[AMMO] Recalling empty drone {drone.drone_id}...")
        await _recall_drone(drone_id=drone.drone_id, producer=producer)
        drone.flight_status = "RETURNING"
        await update_drone_telemetry(drone)
        return

    await _send_drone_waypoint(drone, target, producer)


async def _request_replacement(target, producer: AIOKafkaProducer):
    deploy_cmd = {
        "action": "DEPLOY_DRONE",
        "role": "attack",
        "target_id": target.target_id,
        "position": {"lat": target.position.lat, "lon": target.position.lon}
    }
    await producer.send_and_wait("commands.deployment", json.dumps(deploy_cmd).encode("utf-8"))


async def _recall_drone(drone_id: str, producer: AIOKafkaProducer):
    recall_cmd = {"drone_id": drone_id, "action": "RECALL_DRONE"}
    await producer.send_and_wait("commands.drones", json.dumps(recall_cmd).encode("utf-8"))


async def _send_drone_waypoint(drone, target, producer: AIOKafkaProducer):
    drones_on_target = await get_drones_on_target(drone.assigned_target_id)
    try:
        index = next(i for i, d in enumerate(drones_on_target) if d.drone_id == drone.drone_id)
    except StopIteration:
        index = 0

    waypoint = _calculate_waypoint(target.position, index)

    dist_m = math.sqrt(
        (drone.position.lat - target.position.lat) ** 2 + (drone.position.lon - target.position.lon) ** 2) * 111139
    command_status = "ACTIVE" if dist_m <= 20.0 else "EN_ROUTE"

    cmd = DroneCommand(
        drone_id=drone.drone_id,
        position=waypoint,
        flight_status=command_status
    )
    await producer.send_and_wait("commands.drones", cmd.model_dump_json().encode("utf-8"))

    # Update the drone's status in Redis immediately
    if drone.flight_status != command_status:
        drone.flight_status = command_status
        drone.timestamp = datetime.now(timezone.utc)
        await update_drone_telemetry(drone)


def _calculate_waypoint(target_pos, index: int) -> GeoPoint:
    angle = index * (2 * math.pi / 5)
    offset_lat = STANDOFF_RADIUS_DEG * math.cos(angle)
    offset_lon = STANDOFF_RADIUS_DEG * math.sin(angle)

    return GeoPoint(
        lat=target_pos.lat + offset_lat,
        lon=target_pos.lon + offset_lon,
        alt=150.0 + (index * ALT_SEPARATION)
    )
