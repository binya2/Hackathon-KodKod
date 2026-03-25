# %% Imports
import asyncio
import json
import logging
import os
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from models import TargetTelemetry, NavigationCommand, GeoPoint, DroneTelemetry

# %% Configuration & Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReconBrain")

RECON_ALTITUDE_OFFSET = 200.0

# %% Deployment Environment Detection
RUNNING_IN_K8S = os.environ.get("K8S_DEPLOYMENT", "false").lower() == "true"

# %% Recon Logic & Loop

async def process_target_stream(consumer, producer, drones_registry):
    async for msg in consumer:
        try:
            target = TargetTelemetry(**msg.value)

            # Find active recon drones
            active_recon = [d for d in drones_registry.values() if d.role == "recon" and d.flight_status == "ACTIVE"]

            for drone in active_recon:
                if drone.assigned_target_id != target.target_id:
                    continue
                
                nav_cmd = NavigationCommand(
                    drone_id=drone.drone_id,
                    position=GeoPoint(
                        lat=target.position.lat,
                        lon=target.position.lon,
                        alt=RECON_ALTITUDE_OFFSET
                    ),
                    priority=2
                )
                await producer.send_and_wait("commands.drones", nav_cmd.model_dump(mode='json'))
                # logger.info(f"Recon Brain: Tracking Target {target.target_id} with {drone.drone_id}")

        except Exception as e:
            logger.error(f"Error processing target in Recon Brain: {e}")


async def process_telemetry_stream(consumer, drones_registry):
    async for msg in consumer:
        try:
            tel = DroneTelemetry.model_validate(msg.value)
            drones_registry[tel.drone_id] = tel
        except Exception as e:
            logger.error(f"Error parsing telemetry: {e}")


async def process_deployment_stream(consumer, producer, drones_registry):
    async for msg in consumer:
        try:
            raw_data = json.loads(msg.value.decode("utf-8"))
            role = raw_data.get("role")
            target_id = raw_data.get("target_id")
            if role != "recon":
                continue

            active_recon = [d for d in drones_registry.values() if d.role == "recon" and d.flight_status == "ACTIVE"]

            if len(active_recon) < 5:
                sleeping_recon = [d for d in drones_registry.values() if
                                  d.role == "recon" and d.flight_status == "SLEEP"]
                if sleeping_recon:
                    target_drone = sleeping_recon[0]
                    wake_cmd = {
                        "drone_id": target_drone.drone_id, 
                        "action": "WAKE_UP",
                        "target_id": target_id
                    }
                    await producer.send_and_wait("commands.drones", json.dumps(wake_cmd).encode("utf-8"))
                    logger.info(f"[DEPLOY] Waking up {target_drone.drone_id} for target {target_id}")
                else:
                    logger.warn("[DEPLOY] No sleeping recon drones available.")
            else:
                # Capacity full (5)
                if not RUNNING_IN_K8S:
                    # Docker Compose mode: re-produce to another replica
                    logger.info("[DEPLOY] Recon capacity full (5). Re-producing.")
                    new_key = str(uuid.uuid4()).encode("utf-8")
                    await producer.send_and_wait("commands.deployment", msg.value, key=new_key)
                else:
                    # K8S mode: rely on HPA
                    # logger.info("[K8S SCALE] Capacity full. Relying on K8S HPA to scale pods...")
                    logger.info("[K8S SCALE] Capacity full. Relying on K8S HPA to scale pods...")

        except Exception as e:
            logger.error(f"Error processing deployment: {e}")


async def run_recon_brain():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8") if not isinstance(v, bytes) else v
    )

    target_consumer = AIOKafkaConsumer(
        "target.raw",
        bootstrap_servers=bootstrap_servers,
        group_id="recon_brain_group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    telemetry_consumer = AIOKafkaConsumer(
        "telemetry.raw",
        bootstrap_servers=bootstrap_servers,
        group_id="recon_brain_telemetry",
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    deploy_consumer = AIOKafkaConsumer(
        "commands.deployment",
        bootstrap_servers=bootstrap_servers,
        group_id="recon_deploy"
    )

    await producer.start()
    await target_consumer.start()
    await telemetry_consumer.start()
    await deploy_consumer.start()

    logger.info("Recon Brain service started.")

    try:
        await asyncio.gather(
            process_target_stream(target_consumer, producer, drones_registry),
            process_telemetry_stream(telemetry_consumer, drones_registry),
            process_deployment_stream(deploy_consumer, producer, drones_registry)
        )
    finally:
        await target_consumer.stop()
        await telemetry_consumer.stop()
        await deploy_consumer.stop()
        await producer.stop()


# %% Local Execution Helper
if __name__ == "__main__":
    try:
        asyncio.run(run_recon_brain())
    except KeyboardInterrupt:
        pass
