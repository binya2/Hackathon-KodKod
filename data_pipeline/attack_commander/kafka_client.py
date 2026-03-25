import os
from confluent_kafka import Producer

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
