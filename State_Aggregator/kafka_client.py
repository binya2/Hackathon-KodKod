import json
import logging
from typing import Optional, Any, AsyncGenerator
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer


# %% Kafka Client Factory

class KafkaClientFactory:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self._producer: Optional[AIOKafkaProducer] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_producer(self) -> AIOKafkaProducer:
        """Singleton pattern for AIOKafkaProducer"""
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            await self._producer.start()
            self.logger.info("Kafka Producer started.")
        return self._producer

    def create_consumer(self, topics: list[str], group_id: str) -> AIOKafkaConsumer:
        """Create a new AIOKafkaConsumer instance"""
        return AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode("utf-8"))
        )

    async def close_producer(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None
            self.logger.info("Kafka Producer stopped.")


# %% Kafka Message Loop Pattern

async def message_stream(consumer: AIOKafkaConsumer) -> AsyncGenerator[Any, None]:
    """Helper generator for consumption loop"""
    await consumer.start()
    try:
        async for msg in consumer:
            yield msg.value
    finally:
        await consumer.stop()
