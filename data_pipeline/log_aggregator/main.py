import json
import os

from confluent_kafka import Consumer, KafkaError

# %% Configuration
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = "system.logs"


def run_log_aggregator():
    print(f"[*] Log Aggregator starting... Listening on {KAFKA_BOOTSTRAP} topic: {TOPIC}")

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": "log-aggregator-group",
        "auto.offset.reset": "latest",
        "enable.auto.commit": True
    })
    
    consumer.subscribe([TOPIC])

    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    continue

            try:
                log_data = json.loads(msg.value().decode('utf-8'))
                timestamp = log_data.get("timestamp", "N/A")
                level = log_data.get("level", "INFO")
                service = log_data.get("service", "unknown")
                log_msg = log_data.get("message", "")

                # Formatted console output
                print(f"[{timestamp}] [{level:5}] [{service:16}] {log_msg}")
            except Exception as e:
                print(f"[!] Error parsing message: {e} | value: {msg.value()}")

    except KeyboardInterrupt:
        print("[!] Stopping Log Aggregator...")
    finally:
        consumer.close()


if __name__ == "__main__":
    run_log_aggregator()
