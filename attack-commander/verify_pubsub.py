import argparse
import json

from confluent_kafka import Consumer


def main():
    parser = argparse.ArgumentParser(description="Verify Kafka pub/sub by printing a few messages.")
    parser.add_argument("--kafka-bootstrap", type=str, default=None)
    parser.add_argument("--max-messages", type=int, default=20)
    args = parser.parse_args()

    import os

    bootstrap = args.kafka_bootstrap or os.environ.get("KAFKA_BOOTSTRAP_SERVERS") or "localhost:9092"

    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap,
            "group.id": "verify_pubsub_day1",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )

    topics = ["telemetry.raw", "target.raw"]
    consumer.subscribe(topics)

    received = 0
    print(f"Consuming from {topics} at {bootstrap}")
    print(f"Will exit after {args.max_messages} total messages.")

    try:
        while received < args.max_messages:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Kafka error: {msg.error()}")
                continue

            value_bytes = msg.value()
            if value_bytes is None:
                continue
            value_str = value_bytes.decode("utf-8", errors="replace")

            # Keep printing simple; try JSON pretty formatting.
            try:
                value_json = json.loads(value_str)
                pretty = json.dumps(value_json, separators=(",", ":"), ensure_ascii=False)
            except Exception:
                pretty = value_str

            received += 1
            print(f"[{received}/{args.max_messages}] {msg.topic}: {pretty}")
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()

