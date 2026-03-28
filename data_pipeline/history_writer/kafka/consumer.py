import json
import os
from confluent_kafka import Consumer


def create_history_consumer():
    broker = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    topic = os.getenv('KAFKA_TOPIC', 'aggregated-state-topic')
    group_id = os.getenv('KAFKA_GROUP_ID', 'history-archive-group')
    auto_offset_reset = os.getenv('KAFKA_AUTO_OFFSET_RESET', 'earliest')
    if not broker or not topic:
        raise ValueError('KAFKA_BOOTSTRAP_SERVERS and KAFKA_TOPIC must be set.')
    print(f'[Kafka] Connecting to {broker}, topic: {topic}, group: {group_id}')
    consumer = Consumer({'bootstrap.servers': broker, 'group.id': group_id, 'auto.offset.reset': auto_offset_reset,
                         'enable.auto.commit': True})
    consumer.subscribe([topic])
    return consumer


def poll_and_decode_messages(consumer: Consumer, timeout: float = 1.0):
    msg = consumer.poll(timeout)
    if msg is None:
        return None
    if msg.error():
        print(f'[Kafka] Polling error: {msg.error()}')
        return None
    if msg.value() is None:
        return None
    try:
        return json.loads(msg.value().decode('utf-8'))
    except json.JSONDecodeError as e:
        print(f'[Kafka] JSON decode error: {e}')
        return None
