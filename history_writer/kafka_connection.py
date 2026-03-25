import json
import os

from kafka import KafkaConsumer


def create_consumer():
    broker = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "aggregated-state-topic")
    group_id = os.getenv("KAFKA_GROUP_ID", "history-archive-group")
    auto_offset_reset = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")

    if not broker:
        raise ValueError("KAFKA_BROKER is not set.")
    if not topic:
        raise ValueError("KAFKA_TOPIC is not set.")

    try:
        print(f"[Kafka] Connecting to broker: {broker}, topic: {topic}")
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[broker],
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )
        print("[Kafka] Consumer created successfully.")
        return consumer
    except Exception as exc:
        print(f"[Kafka] Consumer creation failed: {exc}")
        raise
