import json
import logging
from typing import AsyncIterable

from aiokafka import AIOKafkaProducer

from data_pipeline.attack_brain.state_manager import (
    update_target,
    update_drone_telemetry,
    get_active_attack_drones,
    get_sleeping_attack_drones,
)
from data_pipeline.shared_models import TargetTelemetry, DroneTelemetry

logger = logging.getLogger(__name__)


async def process_target_stream(consumer: AsyncIterable):
    """Consumes target data and updates the state."""
    async for msg in consumer:
        if not msg.value:
            continue
        try:
            raw_data = json.loads(msg.value.decode("utf-8"))
            target = TargetTelemetry.model_validate(raw_data)
            update_target(target)
        except Exception as e:
            logger.error("[ERROR] Parsing target: %s", e)


async def process_telemetry_stream(consumer: AsyncIterable):
    """Consumes drone telemetry and updates the state."""
    async for msg in consumer:
        if not msg.value:
            continue
        try:
            raw_data = json.loads(msg.value.decode("utf-8"))
            telemetry = DroneTelemetry.model_validate(raw_data)
            update_drone_telemetry(telemetry)
        except Exception as e:
            logger.error("[ERROR] Parsing telemetry: %s", e)


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
    active_attack_drones = get_active_attack_drones()

    if len(active_attack_drones) < 5:
        await _wake_up_attack_drone(target_id, producer)
    else:
        await _handle_attack_capacity_limit(data, producer, running_in_k8s)


async def _wake_up_attack_drone(target_id: str, producer: AIOKafkaProducer):
    sleeping_drones = get_sleeping_attack_drones()
    if not sleeping_drones:
        logger.warning("[DEPLOY] No sleeping attack drones available.")
        return

    target_drone = sleeping_drones[0]
    target_drone.flight_status = "ACTIVE"
    target_drone.assigned_target_id = target_id
    update_drone_telemetry(target_drone)

    await _send_attack_wake_up_commands(target_drone, target_id, producer)
    logger.info("[DEPLOY] Waking up %s for target %s", target_drone.drone_id, target_id)


async def _send_attack_wake_up_commands(drone: DroneTelemetry, target_id: str, producer: AIOKafkaProducer):
    wake_cmd = {
        "drone_id": drone.drone_id,
        "action": "WAKE_UP",
        "target_id": target_id,
    }
    await producer.send_and_wait("commands.drones", json.dumps(wake_cmd).encode("utf-8"))
    await producer.send_and_wait("telemetry.raw", drone.model_dump_json().encode("utf-8"))


async def _handle_attack_capacity_limit(data: dict, producer: AIOKafkaProducer, running_in_k8s: bool):
    if not running_in_k8s:
        logger.info("[DEPLOY] Capacity full (5). Skipping deployment to avoid infinite loop.")
    else:
        logger.info("[K8S SCALE] Capacity full. Relying on K8S HPA to scale pods...")
