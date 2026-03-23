import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from models import TargetTelemetry, NavigationCommand

# %% Configuration & Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReconBrain")

RECON_DRONE_ID = "RECON_1"
RECON_ALTITUDE_OFFSET = 200.0


# %% Recon Logic & Loop

async def run_recon_brain():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    # Producer for navigation commands
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    # Consumer for target raw data
    consumer = AIOKafkaConsumer(
        "target.raw",
        bootstrap_servers=bootstrap_servers,
        group_id="recon_brain_group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    await producer.start()
    await consumer.start()

    logger.info("Recon Brain service started, monitoring target.raw...")

    try:
        async for msg in consumer:
            try:
                target = TargetTelemetry(**msg.value)

                # Command Logic: Stay 200m above the target's current lat/lon
                nav_cmd = NavigationCommand(
                    drone_id=RECON_DRONE_ID,
                    target_lat=target.position.lat,
                    target_lon=target.position.lon,
                    target_alt=RECON_ALTITUDE_OFFSET,
                    priority=2  # Higher priority for recon tracking
                )

                # Send to commands.drones topic
                await producer.send_and_wait("commands.drones", nav_cmd.model_dump(mode='json'))
                logger.info(
                    f"Recon Brain: Tracking Target {target.target_id} -> Position: {nav_cmd.target_lat}, {nav_cmd.target_lon}, {nav_cmd.target_alt}")

            except Exception as e:
                logger.error(f"Error processing target in Recon Brain: {e}")

    finally:
        await consumer.stop()
        await producer.stop()


# %% Local Execution Helper
# %%
if __name__ == "__main__":
    try:
        asyncio.run(run_recon_brain())
    except KeyboardInterrupt:
        pass
