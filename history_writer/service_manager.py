from db_crud import insert_state_document
from kafka_operations import stream_messages


def run_service():
    print("[Service Manager] History & Archive Service is starting...")

    try:
        for message in stream_messages():
            try:
                if not isinstance(message, dict):
                    print("[Service Manager] Skipping message: payload is not a JSON object.")
                    continue

                print("[Service Manager] Received message, writing to MongoDB...")
                insert_state_document(message)
            except Exception as exc:
                print(f"[Service Manager] Message handling error: {exc}")
    except Exception as exc:
        print(f"[Service Manager] Service loop stopped due to error: {exc}")
        raise
