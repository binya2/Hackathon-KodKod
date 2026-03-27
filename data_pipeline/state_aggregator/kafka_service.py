import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from data_pipeline.shared.models import DroneTelemetry, TargetTelemetry
from data_pipeline.state_aggregator.state_manager import update_drone_telemetry, update_target_telemetry, \
    get_world_state

logger = logging.getLogger(__name__)


async def get_kafka_consumer() -> AIOKafkaConsumer:
    """Configures and returns a Kafka consumer."""
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    return AIOKafkaConsumer(
        "telemetry.raw", "target.raw",
        bootstrap_servers=bootstrap_servers,
        group_id="state_aggregator_group",
        auto_offset_reset="earliest"
    )


async def get_kafka_producer() -> AIOKafkaProducer:
    """Configures and returns a Kafka producer."""
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    return AIOKafkaProducer(bootstrap_servers=bootstrap_servers)


async def process_telemetry_message(raw_data: dict):
    """Parses and updates drone telemetry from raw message data."""
    try:
        tel = DroneTelemetry.model_validate(raw_data)
        await update_drone_telemetry(tel)
    except Exception:
        logger.exception("Error parsing telemetry message")


async def process_target_message(raw_data: dict):
    """Parses and updates target telemetry from raw message data."""
    try:
        tgt = TargetTelemetry.model_validate(raw_data)
        await update_target_telemetry(tgt)
    except Exception:
        logger.exception("Error parsing target message")


async def kafka_consumer_task():
    """Consumes messages from Kafka and updates the global state."""
    consumer = await get_kafka_consumer()
    await consumer.start()
    try:
        async for msg in consumer:
            if not msg.value:
                continue

            try:
                raw_data = json.loads(msg.value.decode("utf-8"))
            except Exception:
                logger.exception("Error decoding JSON from Kafka message")
                continue

            if msg.topic == "telemetry.raw":
                await process_telemetry_message(raw_data)
            elif msg.topic == "target.raw":
                await process_target_message(raw_data)

    finally:
        await consumer.stop()


async def state_publisher_task():
    """Periodically publishes the unified state to Kafka."""
    producer = await get_kafka_producer()
    await producer.start()
    try:
        while True:
            current_state = await get_world_state()
            payload = current_state.model_dump_json()
            await producer.send_and_wait("aggregated-state-topic", payload.encode("utf-8"))
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.info("State publisher task cancelled.")
    finally:
        await producer.stop()
