from db_crud import insert_state_batch
from kafka_operations import stream_messages


# %% Service Management
def run_service():
    print("[Service Manager] History & Archive Service (Buffered) is starting...")
    buffer = []

    try:
        for message in stream_messages():
            try:
                if not isinstance(message, dict):
                    continue

                buffer.append(message)

                if len(buffer) >= 10:
                    print(f"[Service Manager] Buffer full ({len(buffer)}). Flushing to DB...")
                    insert_state_batch(buffer)
                    buffer.clear()

            except Exception as exc:
                print(f"[Service Manager] Message handling error: {exc}")
    except Exception as exc:
        print(f"[Service Manager] Service loop stopped due to error: {exc}")
        raise
