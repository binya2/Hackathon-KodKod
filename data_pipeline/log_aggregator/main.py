import os
import json
from kafka import KafkaConsumer

# %% Configuration
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = "system.logs"

def run_log_aggregator():
    print(f"[*] Log Aggregator starting... Listening on {KAFKA_BOOTSTRAP} topic: {TOPIC}")
    
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='log-aggregator-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    try:
        for message in consumer:
            log_data = message.value
            timestamp = log_data.get("timestamp", "N/A")
            level = log_data.get("level", "INFO")
            service = log_data.get("service", "unknown")
            msg = log_data.get("message", "")
            
            # Formatted console output
            print(f"[{timestamp}] [{level:5}] [{service:16}] {msg}")
    except KeyboardInterrupt:
        print("[!] Stopping Log Aggregator...")
    finally:
        consumer.close()

if __name__ == "__main__":
    run_log_aggregator()
