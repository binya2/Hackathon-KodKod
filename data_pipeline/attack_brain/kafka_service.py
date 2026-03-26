import json
import logging
from datetime import datetime, timezone
from typing import AsyncIterable

from aiokafka import AIOKafkaProducer

from data_pipeline.attack_brain.state_manager import (
    get_active_attack_drones,
    get_sleeping_attack_drones,
)
from data_pipeline.shared_models import DroneTelemetry

logger = logging.getLogger(__name__)


async def process_deployment_stream(consumer: AsyncIterable, producer: AIOKafkaProducer, running_in_k8s: bool):
    """Handles deployment commands to wake up attack drones."""
    async for msg in consumer:
        if not msg.value:
            continue
        try:
            raw_data = json.loads(msg.value.decode("utf-8"))
            if raw_data.get("role") != "attack":
                continue

            await _handle_attack_deployment(raw_data, producer, running_in_k8s)
        except Exception as e:
            logger.error("[ERROR] Parsing deployment: %s", e)


async def _handle_attack_deployment(data: dict, producer: AIOKafkaProducer, running_in_k8s: bool):
    target_id = data.get("target_id")
    sleeping_drones = await get_sleeping_attack_drones()

    if len(sleeping_drones) > 0:
        await _wake_up_attack_drone(target_id, producer)
    else:
        await _handle_attack_capacity_limit(data, producer, running_in_k8s)


async def _wake_up_attack_drone(target_id: str, producer: AIOKafkaProducer):
    sleeping_drones = await get_sleeping_attack_drones()
    if not sleeping_drones:
        return # Double check to avoid race condition

    target_drone = sleeping_drones[0]

    await _send_attack_wake_up_commands(target_drone, target_id, producer)
    logger.info("[DEPLOY] Waking up %s for target %s", target_drone.drone_id, target_id)


async def _send_attack_wake_up_commands(drone: DroneTelemetry, target_id: str, producer: AIOKafkaProducer):
    wake_cmd = {
        "drone_id": drone.drone_id,
        "action": "WAKE_UP",
        "target_id": target_id,
    }
    await producer.send_and_wait("commands.drones", json.dumps(wake_cmd).encode("utf-8"))


async def _handle_attack_capacity_limit(data: dict, producer: AIOKafkaProducer, running_in_k8s: bool):
    if not running_in_k8s:
        logger.info("[DEPLOY] Capacity full (5). Skipping deployment to avoid infinite loop.")
    else:
        logger.info("[K8S SCALE] Capacity full. Relying on K8S HPA to scale pods...")
