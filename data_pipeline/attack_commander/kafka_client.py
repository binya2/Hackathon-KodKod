import json
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

producer: AIOKafkaProducer = None

# הזיכרון המקומי שלנו! (Local Cache) - מתעדכן ברקע כל הזמן
local_world_state = {
    "target_data": [],
    "recon_data": [],
    "attack_data": []
}


def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def init_kafka_producer():
    global producer
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    print(f"[SYSTEM] Attack Commander connecting to Kafka Producer: {bootstrap_servers}")
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await producer.start()


async def stop_kafka_producer():
    global producer
    if producer:
        await producer.stop()


async def consume_state_topic():
    """משימת רקע שמאזינה לסטייט הכללי ומעדכנת את הזיכרון המקומי לטובת ולידציה מהירה"""
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    consumer = AIOKafkaConsumer(
        "aggregated-state-topic",
        bootstrap_servers=bootstrap_servers,
        group_id="attack_commander_cache",
        auto_offset_reset="latest"  # אנחנו צריכים רק את המצב הכי מעודכן
    )
    await consumer.start()
    print("[SYSTEM] Attack Commander State Consumer Started.")
    try:
        async for msg in consumer:
            if msg.value:
                try:
                    state_data = json.loads(msg.value.decode('utf-8'))
                    local_world_state["target_data"] = state_data.get("target_data", [])
                    local_world_state["recon_data"] = state_data.get("recon_data", [])
                    local_world_state["attack_data"] = state_data.get("attack_data", [])
                except Exception as e:
                    print(f"[ERROR] Failed to parse state in Commander: {e}")
    finally:
        await consumer.stop()


async def produce_message(topic: str, key: str, payload: dict):
    if producer:
        key_bytes = key.encode('utf-8') if key else b""
        value_bytes = json.dumps(payload).encode('utf-8')
        await producer.send_and_wait(topic, key=key_bytes, value=value_bytes)


async def log_to_kafka(level: str, message: str, service: str = "attack_commander"):
    payload = {
        "timestamp": iso8601_utc_now(),
        "level": level,
        "service": service,
        "message": message
    }
    await produce_message("system.logs", "", payload)
