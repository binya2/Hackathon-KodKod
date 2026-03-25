import time
from db_crud import insert_state_batch
from kafka_operations import stream_messages


# %% Service Management
def run_service():
    print("[Service Manager] History & Archive Service (Buffered) is starting...")
    buffer = []
    
    # 5 seconds flush timer
    FLUSH_TIMEOUT_SECONDS = 5.0
    last_flush_time = time.time()

    try:
        for message in stream_messages():
            current_time = time.time()
            
            # Message will be None if the poll timed out (1 second)
            if message is not None:
                if isinstance(message, dict):
                    buffer.append(message)
                else:
                    print(f"[Service Manager] Invalid message type {type(message)}, skipping.")

            # Flush condition: Buffer is full OR timeout has passed
            is_full = len(buffer) >= 10
            is_timeout = (current_time - last_flush_time) >= FLUSH_TIMEOUT_SECONDS
            
            if buffer and (is_full or is_timeout):
                reason = "full" if is_full else "timeout"
                print(f"[Service Manager] Buffer {reason} ({len(buffer)}). Flushing to DB...")
                insert_state_batch(buffer)
                buffer.clear()
                last_flush_time = current_time

    except Exception as exc:
        print(f"[Service Manager] Service loop stopped due to error: {exc}")
        raise