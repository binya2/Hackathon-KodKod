import json
from kafka_connection import create_consumer

def stream_messages():
    consumer = create_consumer()
    print('[Kafka Operations] Starting message polling loop...')
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                yield None
                continue
            if msg.error():
                print(f'[Kafka Operations] Polling error: {msg.error()}')
                continue
            if msg.value() is None:
                print('[Kafka Operations] Skipping empty message.')
                continue
            try:
                decoded_value = msg.value().decode('utf-8')
                json_value = json.loads(decoded_value)
                yield json_value
            except json.JSONDecodeError as json_err:
                print(f'[Kafka Operations] JSON decode error: {json_err} for value: {msg.value()}')
            except Exception as e:
                print(f'[Kafka Operations] Message processing error: {e}')
    finally:
        consumer.close()