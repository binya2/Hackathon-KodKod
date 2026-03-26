import asyncio
import logging
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from data_pipeline.attack_brain.assignment_logic import assignment_loop
from data_pipeline.attack_brain.kafka_service import (
    process_deployment_stream,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("attack-brain")

RUNNING_IN_K8S = os.environ.get("K8S_DEPLOYMENT", "false").lower() == "true"


async def main():
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    logger.info("[SYSTEM] Connecting to Kafka at %s", bootstrap)

    deploy_consumer = AIOKafkaConsumer("commands.deployment", bootstrap_servers=bootstrap, group_id="attack_deploy",
                                       auto_offset_reset="earliest")
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap)

    await deploy_consumer.start()
    await producer.start()

    logger.info("[SYSTEM] Attack Brain Microservice Started.")

    try:
        await asyncio.gather(
            process_deployment_stream(deploy_consumer, producer, RUNNING_IN_K8S),
            assignment_loop(producer)
        )
    finally:
        await deploy_consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
