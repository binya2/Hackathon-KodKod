import asyncio
import logging
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from data_pipeline.attack_brain.assignment_logic import assignment_loop
from data_pipeline.attack_brain.kafka_service import (
    process_target_stream,
    process_telemetry_stream,
    process_deployment_stream,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("attack-brain")

RUNNING_IN_K8S = os.environ.get("K8S_DEPLOYMENT", "false").lower() == "true"


async def main():
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    logger.info("[SYSTEM] Connecting to Kafka at %s", bootstrap)

    target_consumer = AIOKafkaConsumer("target.raw", bootstrap_servers=bootstrap, group_id="attack-brain-target",
                                       auto_offset_reset="earliest")
    telemetry_consumer = AIOKafkaConsumer("telemetry.raw", bootstrap_servers=bootstrap,
                                          group_id="attack-brain-telemetry", auto_offset_reset="earliest")
    deploy_consumer = AIOKafkaConsumer("commands.deployment", bootstrap_servers=bootstrap, group_id="attack_deploy",
                                       auto_offset_reset="earliest")
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
            process_deployment_stream(deploy_consumer, producer, RUNNING_IN_K8S),
            assignment_loop(producer)
        )
    finally:
        await target_consumer.stop()
        await telemetry_consumer.stop()
        await deploy_consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
