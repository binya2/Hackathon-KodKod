import json
import os
from datetime import datetime, timezone
from data_pipeline.shared.kafka_utils import get_kafka_producer, AIOKafkaProducer

producer: AIOKafkaProducer = None


def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


async def init_kafka_producer():
    global producer
    bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    print(f'[SYSTEM] Attack Commander connecting to Kafka Producer: {bootstrap_servers}')
    producer = await get_kafka_producer(bootstrap_servers)
    await producer.start()


async def stop_kafka_producer():
    global producer
    if producer:
        await producer.stop()


async def produce_message(topic: str, key: str, payload: dict):
    if producer:
        key_bytes = key.encode('utf-8') if key else b''
        value_bytes = json.dumps(payload).encode('utf-8')
        await producer.send_and_wait(topic, key=key_bytes, value=value_bytes)


async def log_to_kafka(level: str, message: str, service: str = 'attack_commander'):
    payload = {'timestamp': iso8601_utc_now(), 'level': level, 'service': service, 'message': message}
    await produce_message('system.logs', '', payload)
