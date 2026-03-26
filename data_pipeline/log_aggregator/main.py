import os
from kafka_service import create_consumer, poll_logs
from formatter import print_log


def main():
    kafka_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = "system.logs"
    group_id = "log-aggregator-group"

    print(f"[*] Log Aggregator starting... Listening on {kafka_bootstrap} topic: {topic}")

    consumer = create_consumer(kafka_bootstrap, group_id, topic)
    poll_logs(consumer, print_log)


if __name__ == "__main__":
    main()
