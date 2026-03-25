import os
import json
from datetime import datetime, timezone
from confluent_kafka import Producer


# %% Utils

def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# %% Kafka Client Setup

def delivery_report(err, msg):
    if err is not None:
        print(f"[KAFKA-PRODUCER] Failed: {err}")
    else:
        print(f"[KAFKA-PRODUCER] Message sent to {msg.topic()} [{msg.partition()}]")


def get_producer() -> Producer:
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    print(f"[SYSTEM] Attack Commander connecting to Kafka: {bootstrap_servers}")

    producer_conf = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "attack-commander",
        "allow.auto.create.topics": "true"
    }
    return Producer(producer_conf)


# Singleton instance
producer = get_producer()


def log_to_kafka(level: str, message: str, service: str = "attack_commander"):
    """
    Produces a log message to the system.logs topic.
    """
    payload = {
        "timestamp": iso8601_utc_now(),
        "level": level,
        "service": service,
        "message": message
    }
    try:
        producer.produce(
            topic="system.logs",
            value=json.dumps(payload),
            callback=delivery_report
        )
        producer.poll(0)  # Serve delivery callbacks
    except Exception as e:
        print(f"[LOGGING ERROR] Failed to produce log to Kafka: {e}")
