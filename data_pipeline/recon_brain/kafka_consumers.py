import json
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import AsyncIterable, Dict
from aiokafka import AIOKafkaProducer

from data_pipeline.shared_models import TargetTelemetry, NavigationCommand, GeoPoint, DroneTelemetry
from data_pipeline.recon_brain.state_manager import (
    update_drone_telemetry,
    get_active_recon_drone_for_target,
    get_active_recon_drones,
    get_sleeping_recon_drones
)

logger = logging.getLogger(__name__)

RECON_ALTITUDE_OFFSET = 200.0
_last_recon_nav_command_time: Dict[str, float] = {}


async def process_target_stream(consumer: AsyncIterable, producer: AIOKafkaProducer):
    """Processes incoming target telemetry and issues navigation commands to assigned recon drones."""
    async for msg in consumer:
        if not msg.value:
            continue
        try:
            raw_data = json.loads(msg.value.decode("utf-8"))
            target = TargetTelemetry(**raw_data)

            if target.target_id == "TGT-INIT":
                continue

            if target.health <= 0:
                active_recon = await get_active_recon_drone_for_target(target.target_id)
                for drone in active_recon:
                    logger.info(f"[AUTO-RECALL] Target {target.target_id} destroyed. Recalling recon drone {drone.drone_id}")
                    recall_cmd = {
                        "drone_id": drone.drone_id,
                        "action": "RECALL_DRONE"
                    }
                    await producer.send_and_wait("commands.drones", json.dumps(recall_cmd).encode("utf-8"))

                    # Optimistic update
                    drone.flight_status = "RETURNING"
                    drone.assigned_target_id = None
                    drone.timestamp = datetime.now(timezone.utc)
                    await update_drone_telemetry(drone)
                continue

            active_recon = await get_active_recon_drone_for_target(target.target_id)

            for i, drone in enumerate(active_recon):
                now = time.time()
                last_time = _last_recon_nav_command_time.get(drone.drone_id, 0)
                if now - last_time < 1.0:
                    continue

                # Standoff offset for recon: approx 15m East and 15m North
                # This ensures they aren't directly overhead
                nav_cmd = NavigationCommand(
                    drone_id=drone.drone_id,
                    position=GeoPoint(
                        lat=target.position.lat + 0.00015,
                        lon=target.position.lon + 0.00015,
                        alt=RECON_ALTITUDE_OFFSET + (i * 10.0)
                    ),
                    priority=2
                )
                await producer.send_and_wait("commands.drones", nav_cmd.model_dump_json().encode("utf-8"))
                _last_recon_nav_command_time[drone.drone_id] = now

        except Exception as e:
            logger.error("Error processing target in Recon Brain: %s", e)


async def process_deployment_stream(consumer: AsyncIterable, producer: AIOKafkaProducer, running_in_k8s: bool):
    """Processes deployment commands to wake up recon drones and assign them to targets."""
    async for msg in consumer:
        if not msg.value:
            continue
        try:
            raw_data = json.loads(msg.value.decode("utf-8"))
            if raw_data.get("role") != "recon":
                continue

            await _handle_recon_deployment(raw_data, producer, running_in_k8s)
        except Exception as e:
            logger.error("Error processing deployment in Recon Brain: %s", e)


async def _handle_recon_deployment(data: dict, producer: AIOKafkaProducer, running_in_k8s: bool):
    target_id = data.get("target_id")
    sleeping_recon = await get_sleeping_recon_drones()

    if len(sleeping_recon) > 0:
        await _wake_up_recon_drone(target_id, producer)
    else:
        await _handle_capacity_limit(data, producer, running_in_k8s)


async def _wake_up_recon_drone(target_id: str, producer: AIOKafkaProducer):
    sleeping_recon = await get_sleeping_recon_drones()
    if not sleeping_recon:
        return # Double check to avoid race condition

    target_drone = sleeping_recon[0]
    target_drone.flight_status = "EN_ROUTE"
    target_drone.assigned_target_id = target_id
    target_drone.timestamp = datetime.now(timezone.utc)
    await update_drone_telemetry(target_drone)

    await _send_wake_up_commands(target_drone, target_id, producer)
    logger.info("[DEPLOY] Waking up %s for target %s", target_drone.drone_id, target_id)


async def _send_wake_up_commands(drone: DroneTelemetry, target_id: str, producer: AIOKafkaProducer):
    wake_cmd = {
        "drone_id": drone.drone_id,
        "action": "WAKE_UP",
        "target_id": target_id
    }
    await producer.send_and_wait("commands.drones", json.dumps(wake_cmd).encode("utf-8"))
    await producer.send_and_wait("telemetry.raw", drone.model_dump_json().encode("utf-8"))


async def _handle_capacity_limit(data: dict, producer: AIOKafkaProducer, running_in_k8s: bool):
    if not running_in_k8s:
        logger.info("[DEPLOY] Recon capacity full (5). Skipping deployment to avoid infinite loop.")
    else:
        logger.info("[K8S SCALE] Capacity full. Relying on K8S HPA to scale pods...")
