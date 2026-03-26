import time
from kafka_service import create_history_consumer, poll_and_decode_messages
from db_service import archive_state_batch


class HistoryService:
    def __init__(self, buffer_size: int = 10, flush_interval: float = 5.0):
        self.buffer = []
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.last_flush_time = time.time()
        self.consumer = create_history_consumer()

    def run(self):
        print("[History] Service started.")
        try:
            while True:
                message = poll_and_decode_messages(self.consumer)
                if message:
                    self.buffer.append(message)

                if self._should_flush():
                    self._flush_buffer()
        finally:
            self.consumer.close()

    def _should_flush(self):
        is_full = len(self.buffer) >= self.buffer_size
        is_timeout = (time.time() - self.last_flush_time) >= self.flush_interval
        return self.buffer and (is_full or is_timeout)

    def _flush_buffer(self):
        archive_state_batch(self.buffer)
        self.buffer.clear()
        self.last_flush_time = time.time()


def run_history_service():
    service = HistoryService()
    service.run()
