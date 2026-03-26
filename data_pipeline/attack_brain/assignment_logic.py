import asyncio
import json
import logging
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

import math

ALT_SEPARATION = 20.0
# Standoff radius: ~5 meters in degrees
STANDOFF_RADIUS = 0.00005


async def assignment_loop(producer: AIOKafkaProducer):
    """Continuously evaluates drone positions relative to their assigned targets."""
    while True:
        # Get all attack drones that are either active or currently being deployed
        all_drones = await get_active_attack_drones()
        active_targets = await get_active_targets()

        # 1. Target-centric check: Ensure each active target has 2 drones
        for target in active_targets:
            if target.target_id == "TGT-INIT":
                continue
            assigned_count = sum(
                1 for d in all_drones
                if d.assigned_target_id == target.target_id and d.flight_status in ["ACTIVE", "ATTACKING"]
            )
            if assigned_count < 2:
                logger.info(f"[ASSIGN] Target {target.target_id} has {assigned_count} drones. Requesting replacement...")
                await _request_replacement(target.target_id, producer)

        # 2. Drone-centric check: Process assignments
        active_attack_drones = [d for d in all_drones if d.assigned_target_id and d.flight_status != "RETURNING"]
        for drone in active_attack_drones:
            await _process_drone_assignment(drone, producer, all_drones, active_targets)

        await asyncio.sleep(2.0)


async def _process_drone_assignment(drone, producer: AIOKafkaProducer, all_drones, active_targets):
    target = await get_target(drone.assigned_target_id)

    # If target is missing or dead, try to find a new one
    if not target or target.health <= 0:
        new_target = next(
            (t for t in active_targets if sum(
                1 for d in all_drones
                if d.assigned_target_id == t.target_id and d.flight_status in ["ACTIVE", "ATTACKING"]
            ) < 2),
            None
        )

        if new_target:
            logger.info(f"[RE-ASSIGN] Drone {drone.drone_id} moved from dead {drone.assigned_target_id} to {new_target.target_id}")
            drone.assigned_target_id = new_target.target_id
            drone.timestamp = datetime.now(timezone.utc)
            await update_drone_telemetry(drone)
            target = new_target # Continue processing with new target
        else:
            await _recall_drone(drone.drone_id, producer)
            return

    # Skip updates if drone is attacking
    if drone.flight_status == "ATTACKING":
        return

    # Check for empty ammo and replace
    if drone.role == "attack" and drone.weapons_count == 0:
        # Check if a replacement is already assigned to this target
        replacement_already_sent = any(
            d.assigned_target_id == drone.assigned_target_id and
            d.drone_id != drone.drone_id and
            d.flight_status in ["ACTIVE", "ATTACKING"]
            for d in all_drones
        )

        if not replacement_already_sent:
            logger.info(
                f"[AMMO] Drone {drone.drone_id} out of ammo. Requesting replacement for {drone.assigned_target_id}...")
            await _request_replacement(drone.assigned_target_id, producer)

        # Recall the empty drone
        logger.info(f"[AMMO] Drone {drone.drone_id} is empty. Recalling...")
        await _recall_drone(drone_id=drone.drone_id, producer=producer)

        # Mark locally to avoid re-processing in this loop
        drone.flight_status = "RETURNING"
        drone.assigned_target_id = None
        drone.timestamp = datetime.now(timezone.utc)
        await update_drone_telemetry(drone)
        return

    await _send_drone_waypoint(drone, target, producer)


async def _request_replacement(target_id: str, producer: AIOKafkaProducer):
    deploy_cmd = {
        "action": "DEPLOY_DRONE",
        "role": "attack",
        "target_id": target_id
    }
    await producer.send_and_wait("commands.deployment", json.dumps(deploy_cmd).encode("utf-8"))


async def _recall_drone(drone_id: str, producer: AIOKafkaProducer):
    recall_cmd = {
        "drone_id": drone_id,
        "action": "RECALL_DRONE"
    }
    await producer.send_and_wait("commands.drones", json.dumps(recall_cmd).encode("utf-8"))


async def _send_drone_waypoint(drone, target, producer: AIOKafkaProducer):
    drones_on_target = await get_drones_on_target(drone.assigned_target_id)

    try:
        index = next(i for i, d in enumerate(drones_on_target) if d.drone_id == drone.drone_id)
    except StopIteration:
        index = 0

    waypoint = _calculate_waypoint(target.position, index)
    cmd = DroneCommand(drone_id=drone.drone_id, position=waypoint)
    await producer.send_and_wait("commands.drones", cmd.model_dump_json().encode("utf-8"))


def _calculate_waypoint(target_pos, index: int) -> GeoPoint:
    # Circle the target at 15m radius
    angle = index * (2 * math.pi / 5)
    offset_lat = STANDOFF_RADIUS * math.cos(angle)
    offset_lon = STANDOFF_RADIUS * math.sin(angle)

    return GeoPoint(
        lat=target_pos.lat + offset_lat,
        lon=target_pos.lon + offset_lon,
        alt=150.0 + (index * ALT_SEPARATION)
    )
