# %% Imports
import asyncio
import json
import logging
import os
import uuid
from typing import AsyncIterable

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from data_pipeline.shared_models import TargetTelemetry, DroneTelemetry, GeoPoint, DroneCommand

# %% Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("attack-brain")

# %% Deployment Environment Detection
RUNNING_IN_K8S = os.environ.get("K8S_DEPLOYMENT", "false").lower() == "true"

# %% Global State
targets = {}
drones_registry = {}  # drone_id -> DroneTelemetry


# %% Logic Loop
async def process_target_stream(consumer: AsyncIterable):
    async for msg in consumer:
        try:
            if not msg.value:
                continue
            raw_data = json.loads(msg.value.decode("utf-8"))
            target = TargetTelemetry.model_validate(raw_data)
            targets[target.target_id] = target
        except Exception as e:
            logger.error(f"[ERROR] Parsing target: {e}")


async def process_telemetry_stream(consumer: AsyncIterable):
    async for msg in consumer:
        try:
            if not msg.value:
                continue
            raw_data = json.loads(msg.value.decode("utf-8"))
            telemetry = DroneTelemetry.model_validate(raw_data)
            drones_registry[telemetry.drone_id] = telemetry
        except Exception as e:
            logger.error(f"[ERROR] Parsing telemetry: {e}")


async def process_deployment_stream(consumer: AsyncIterable, producer):
    async for msg in consumer:
        try:
            if not msg.value:
                continue
            raw_data = json.loads(msg.value.decode("utf-8"))
            role = raw_data.get("role")
            target_id = raw_data.get("target_id")
            if role != "attack":
                continue

            active_attack_drones = [
                d for d in drones_registry.values()
                if d.role == "attack" and d.flight_status == "ACTIVE"
            ]

            if len(active_attack_drones) < 5:
                sleeping_drones = [
                    d for d in drones_registry.values()
                    if d.role == "attack" and d.flight_status == "SLEEP"
                ]
                if sleeping_drones:
                    target_drone = sleeping_drones[0]
                    target_drone.flight_status = "ACTIVE"
                    target_drone.assigned_target_id = target_id
                    wake_cmd = {
                        "drone_id": target_drone.drone_id,
                        "action": "WAKE_UP",
                        "target_id": target_id
                    }
                    await producer.send_and_wait("commands.drones", json.dumps(wake_cmd).encode("utf-8"))
                    await producer.send_and_wait("telemetry.raw", target_drone.model_dump_json().encode("utf-8"))
                    logger.info(f"[DEPLOY] Waking up {target_drone.drone_id} for target {target_id}")
                else:
                    logger.warning("[DEPLOY] No sleeping attack drones available.")
            else:
                if not RUNNING_IN_K8S:
                    logger.info("[DEPLOY] Capacity full (5). Re-producing for other replicas.")
                    new_key = str(uuid.uuid4()).encode("utf-8")
                    await producer.send_and_wait("commands.deployment", msg.value, key=new_key)
                else:
                    logger.info("[K8S SCALE] Capacity full. Relying on K8S HPA to scale pods...")

        except Exception as e:
            logger.error(f"[ERROR] Parsing deployment: {e}")


async def assignment_loop(producer):
    alt_separation = 20.0
    while True:
        active_attack_drones = [
            d for d in drones_registry.values()
            if d.role == "attack" and d.flight_status == "ACTIVE" and d.assigned_target_id
        ]

        for drone in active_attack_drones:
            target = targets.get(drone.assigned_target_id)
            if not target or target.health <= 0:
                recall_cmd = {
                    "drone_id": drone.drone_id,
                    "action": "RECALL_DRONE"
                }
                await producer.send_and_wait("commands.drones", json.dumps(recall_cmd).encode("utf-8"))
                continue

            drones_on_target = [d for d in active_attack_drones if d.assigned_target_id == drone.assigned_target_id]
            try:
                i = drones_on_target.index(drone)
            except ValueError:
                i = 0

            offset_lat = 0.0005 * (i % 2 if i % 2 != 0 else -1)
            offset_lon = 0.0005 * (1 if i > 1 else -1)

            target_pos = target.position
            waypoint = GeoPoint(
                lat=target_pos.lat + offset_lat,
                lon=target_pos.lon + offset_lon,
                alt=150.0 + (i * alt_separation)
            )

            cmd = DroneCommand(drone_id=drone.drone_id, position=waypoint)
            await producer.send_and_wait("commands.drones", cmd.model_dump_json().encode("utf-8"))

        await asyncio.sleep(2.0)


# %% Main Execution
async def main():
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    logger.info(f"[SYSTEM] Connecting to Kafka at {bootstrap}")

    target_consumer = AIOKafkaConsumer("target.raw", bootstrap_servers=bootstrap, group_id="attack-brain-target")
    telemetry_consumer = AIOKafkaConsumer("telemetry.raw", bootstrap_servers=bootstrap,
                                          group_id="attack-brain-telemetry")
    deploy_consumer = AIOKafkaConsumer("commands.deployment", bootstrap_servers=bootstrap, group_id="attack_deploy")
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap)

    await target_consumer.start()
    await telemetry_consumer.start()
    await deploy_consumer.start()
    await producer.start()

    logger.info("[SYSTEM] Attack Brain Microservice Started.")

    try:
        await asyncio.gather(
            process_target_stream(target_consumer),
            process_telemetry_stream(telemetry_consumer),
            process_deployment_stream(deploy_consumer, producer),
            assignment_loop(producer)
        )
    finally:
        await target_consumer.stop()
        await telemetry_consumer.stop()
        await deploy_consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
