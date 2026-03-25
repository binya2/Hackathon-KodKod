import asyncio
import logging
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from data_pipeline.recon_brain.kafka_consumers import (
    process_target_stream,
    process_telemetry_stream,
    process_deployment_stream
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReconBrain")

RUNNING_IN_K8S = os.environ.get("K8S_DEPLOYMENT", "false").lower() == "true"


async def run_recon_brain():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)

    target_consumer = AIOKafkaConsumer(
        "target.raw",
        bootstrap_servers=bootstrap_servers,
        group_id="recon_brain_group",
        auto_offset_reset="earliest"
    )

    telemetry_consumer = AIOKafkaConsumer(
        "telemetry.raw",
        bootstrap_servers=bootstrap_servers,
        group_id="recon_brain_telemetry",
        auto_offset_reset="earliest"
    )

    deploy_consumer = AIOKafkaConsumer(
        "commands.deployment",
        bootstrap_servers=bootstrap_servers,
        group_id="recon_deploy",
        auto_offset_reset="earliest"
    )

    await producer.start()
    await target_consumer.start()
    await telemetry_consumer.start()
    await deploy_consumer.start()

    logger.info("Recon Brain service started.")

    try:
        await asyncio.gather(
            process_target_stream(target_consumer, producer),
            process_telemetry_stream(telemetry_consumer),
            process_deployment_stream(deploy_consumer, producer, RUNNING_IN_K8S)
        )
    finally:
        await target_consumer.stop()
        await telemetry_consumer.stop()
        await deploy_consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    try:
        asyncio.run(run_recon_brain())
    except KeyboardInterrupt:
        logger.info("Service stopped manually by user.")
