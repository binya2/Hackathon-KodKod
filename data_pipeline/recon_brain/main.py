import asyncio

import logging

import os

from data_pipeline.recon_brain.kafka_consumers import process_target_stream, process_deployment_stream

from data_pipeline.shared.kafka_utils import get_kafka_producer, get_kafka_consumer

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('ReconBrain')

RUNNING_IN_K8S = os.environ.get('K8S_DEPLOYMENT', 'false').lower() == 'true'


async def run_recon_brain():
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    producer = await get_kafka_producer(bootstrap_servers)
    target_consumer = await get_kafka_consumer(['target.raw'], bootstrap_servers=bootstrap_servers,
                                               group_id='recon_brain_group', offset_reset='earliest')
    deploy_consumer = await get_kafka_consumer(['commands.deployment'], bootstrap_servers=bootstrap_servers,
                                               group_id='recon_deploy', offset_reset='earliest')
    await producer.start()
    await target_consumer.start()
    await deploy_consumer.start()
    logger.info('Recon Brain service started.')
    try:
        await asyncio.gather(process_target_stream(target_consumer, producer),
                             process_deployment_stream(deploy_consumer, producer, RUNNING_IN_K8S))
    finally:
        await target_consumer.stop()
        await deploy_consumer.stop()
        await producer.stop()


if __name__ == '__main__':
    try:
        asyncio.run(run_recon_brain())
    except KeyboardInterrupt:
        logger.info('Service stopped manually by user.')
