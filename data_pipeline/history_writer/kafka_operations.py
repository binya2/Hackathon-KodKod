from kafka_connection import create_consumer


def stream_messages():
    consumer = create_consumer()
    print("[Kafka Operations] Starting message polling loop...")

    while True:
        try:
            polled_records = consumer.poll(timeout_ms=1000)

            if not polled_records:
                continue

            for _, records in polled_records.items():
                for record in records:
                    if record.value is None:
                        print("[Kafka Operations] Skipping empty message.")
                        continue
                    yield record.value
        except Exception as exc:
            print(f"[Kafka Operations] Polling error: {exc}")
