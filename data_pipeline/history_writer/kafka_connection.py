import os

from confluent_kafka import Consumer


def create_consumer():
    broker = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "aggregated-state-topic")
    group_id = os.getenv("KAFKA_GROUP_ID", "history-archive-group")
    auto_offset_reset = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")

    if not broker:
        raise ValueError("KAFKA_BOOTSTRAP_SERVERS is not set.")
    if not topic:
        raise ValueError("KAFKA_TOPIC is not set.")

    try:
        print(f"[Kafka] Connecting to broker: {broker}, topic: {topic}")
        consumer = Consumer({
            "bootstrap.servers": broker,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": True
        })
        consumer.subscribe([topic])
        print("[Kafka] Consumer created successfully.")
        return consumer
    except Exception as exc:
        print(f"[Kafka] Consumer creation failed: {exc}")
        raise
