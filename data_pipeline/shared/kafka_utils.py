from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

__all__ = ["AIOKafkaConsumer", "AIOKafkaProducer", "get_kafka_producer", "get_kafka_consumer"]

async def get_kafka_producer(bootstrap_servers: str) -> AIOKafkaProducer:
    """Configures and returns a Kafka producer."""
    return AIOKafkaProducer(bootstrap_servers=bootstrap_servers)

async def get_kafka_consumer(topics: list, group_id: str, bootstrap_servers: str, offset_reset: str = 'earliest') -> AIOKafkaConsumer:
    """Configures and returns a Kafka consumer."""
    return AIOKafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset=offset_reset
    )
