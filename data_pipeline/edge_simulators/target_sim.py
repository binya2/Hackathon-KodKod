import argparse
import json
import os
import time
import random
from target_model import TargetState
from target_kafka import create_target_producer, create_target_consumer
from target_logic import handle_target_event


def main():
    parser = argparse.ArgumentParser(description="Target Simulator")
    parser.add_argument("--kafka-bootstrap", type=str,
                        default=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    args = parser.parse_args()

    producer = create_target_producer(args.kafka_bootstrap)
    consumer = create_target_consumer(args.kafka_bootstrap)
    state = TargetState()

    print(f"[TARGET] Simulator running. Connecting to {args.kafka_bootstrap}")

    try:
        while True:
            _poll_events(consumer, state, producer)
            _emit_telemetry(state, producer)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[SYSTEM] Stopped manually.")
    finally:
        producer.flush()
        consumer.close()


def _poll_events(consumer, state, producer):
    msg = consumer.poll(0.01)
    if msg and not msg.error():
        try:
            event_data = json.loads(msg.value().decode("utf-8"))
            handle_target_event(event_data, msg.topic(), state, producer)
        except Exception as e:
            print(f"[Error] Failed to process event: {e}")


def _emit_telemetry(state, producer):
    if not state.is_active:
        if state._death_broadcasted:
            return
        state._death_broadcasted = True

    jitter_lat = state.base_lat + random.uniform(-0.00002, 0.00002)
    jitter_lon = state.base_lon + random.uniform(-0.00002, 0.00002)

    telemetry = state.create_telemetry(jitter_lat, jitter_lon)
    producer.produce("target.raw", key=state.target_id, value=telemetry.model_dump_json())
    producer.poll(0)


if __name__ == "__main__":
    main()
