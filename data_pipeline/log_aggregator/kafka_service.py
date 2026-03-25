import json
from confluent_kafka import Consumer, KafkaError


def create_consumer(bootstrap_servers: str, group_id: str, topic: str):
    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True
    })
    consumer.subscribe([topic])
    return consumer


def poll_logs(consumer: Consumer, callback, timeout: float = 1.0):
    try:
        while True:
            msg = consumer.poll(timeout)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"Consumer error: {msg.error()}")
                continue

            try:
                log_data = json.loads(msg.value().decode('utf-8'))
                callback(log_data)
            except Exception as e:
                print(f"[!] Error parsing message: {e} | value: {msg.value()}")

    except KeyboardInterrupt:
        print("[!] Stopping Log Aggregator...")
    finally:
        consumer.close()
