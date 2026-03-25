# %% Imports
import argparse
import json
import random
import time
import os
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel
from confluent_kafka import Producer, Consumer

# %% Data Contracts
class GeoPoint(BaseModel):
    lat: float
    lon: float

class TargetTelemetry(BaseModel):
    target_id: str
    target_type: str = "vehicle"
    position: GeoPoint
    confidence: float
    health: float = 100.0
    timestamp: str

# %% State Management
class TargetState:
    def __init__(self):
        self.base_lat: float = 31.705
        self.base_lon: float = 35.205
        self.health: float = 100.0
        self.is_active: bool = False

# %% Utils
def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# %% Kafka Logic
def setup_kafka_clients(bootstrap_servers: str) -> tuple[Producer, Consumer]:
    producer = Producer({"bootstrap.servers": bootstrap_servers})
    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers,
        "group.id": f"target-sim-{random.randint(0, 1000)}",
        "auto.offset.reset": "latest"
    })
    consumer.subscribe(["events.payload_dropped", "events.intel"])
    return producer, consumer

def process_target_event(event_data: Dict[str, Any], topic: str, state: TargetState, producer: Producer):
    if topic == "events.payload_dropped":
        if not state.is_active:
            return
        d_lat = event_data.get("lat")
        d_lon = event_data.get("lon")
        # Euclidean distance check
        dist = math.sqrt((state.base_lat - d_lat) ** 2 + (state.base_lon - d_lon) ** 2)
        if dist < 0.001:  # ~100m
            state.health -= 25.0
            print(f"💥 [HIT] Target TGT-1 hit by {event_data.get('drone_id')}! Health: {state.health}")
            if state.health <= 0:
                print("💀 [DESTROYED] TGT-1 eliminated.")
                state.health = 0
    
    elif topic == "events.intel":
        if event_data.get("action") == "SPAWN_TARGET":
            state.base_lat = event_data.get("lat")
            state.base_lon = event_data.get("lon")
            state.health = 100.0
            state.is_active = True
            print(f"🎯 [SPAWN] Target TGT-1 spawned at {state.base_lat}, {state.base_lon}")
            
            # Zero-latency UI update: produce first telemetry immediately
            initial_telemetry = TargetTelemetry(
                target_id="TGT-1",
                target_type="vehicle",
                position=GeoPoint(lat=state.base_lat, lon=state.base_lon),
                confidence=0.95,
                health=state.health,
                timestamp=iso8601_utc_now()
            )
            producer.produce("target.raw", key="TGT-1", value=initial_telemetry.model_dump_json())
            producer.poll(0)

# %% Main Execution
def main():
    parser = argparse.ArgumentParser(description="Target Simulator")
    parser.add_argument("--kafka-bootstrap", type=str,
                        default=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    args = parser.parse_args()

    producer, consumer = setup_kafka_clients(args.kafka_bootstrap)
    state = TargetState()

    print(f"[TARGET] Simulating Target TGT-1. Connecting to {args.kafka_bootstrap}")

    try:
        while True:
            # 1. Check for hits or spawn events
            msg = consumer.poll(0.01)
            if msg and not msg.error():
                event_data = json.loads(msg.value().decode("utf-8"))
                process_target_event(event_data, msg.topic(), state, producer)

            # 2. Produce telemetry only if active
            if state.is_active:
                lat = state.base_lat + random.uniform(-0.0001, 0.0001)
                lon = state.base_lon + random.uniform(-0.0001, 0.0001)

                telemetry = TargetTelemetry(
                    target_id="TGT-1",
                    target_type="vehicle",
                    position=GeoPoint(lat=lat, lon=lon),
                    confidence=0.95 if state.health > 0 else 0.0,
                    health=state.health,
                    timestamp=iso8601_utc_now()
                )

                producer.produce("target.raw", key="TGT-1", value=telemetry.model_dump_json())
                producer.poll(0)
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        consumer.close()

if __name__ == "__main__":
    main()
