# %% Imports
import argparse
import json
import random
import time
import os
import math
from datetime import datetime, timezone
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
    timestamp: str


# %% Utils
def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# %% Main Execution
def main():
    parser = argparse.ArgumentParser(description="Target Simulator")
    parser.add_argument("--kafka-bootstrap", type=str,
                        default=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    args = parser.parse_args()

    producer = Producer({"bootstrap.servers": args.kafka_bootstrap})
    consumer = Consumer({
        "bootstrap.servers": args.kafka_bootstrap,
        "group.id": f"target-sim-{random.randint(0, 1000)}",
        "auto.offset.reset": "latest"
    })
    consumer.subscribe(["events.payload_dropped", "events.intel"])

    # State
    base_lat, base_lon = 31.705, 35.205
    health = 100.0
    is_active = False

    print(f"[TARGET] Simulating Target TGT-1. Connecting to {args.kafka_bootstrap}")

    try:
        while True:
            # 1. Check for hits or spawn events
            msg = consumer.poll(0.01)
            if msg and not msg.error():
                event = json.loads(msg.value().decode("utf-8"))
                
                if msg.topic() == "events.payload_dropped":
                    if not is_active:
                        continue
                    d_lat = event.get("lat")
                    d_lon = event.get("lon")
                    # Euclidean distance check
                    dist = math.sqrt((base_lat - d_lat) ** 2 + (base_lon - d_lon) ** 2)
                    if dist < 0.001:  # ~100m
                        health -= 25.0
                        print(f"💥 [HIT] Target TGT-1 hit by {event.get('drone_id')}! Health: {health}")
                        if health <= 0:
                            print("💀 [DESTROYED] TGT-1 eliminated.")
                            health = 0
                
                elif msg.topic() == "events.intel":
                    if event.get("action") == "SPAWN_TARGET":
                        base_lat = event.get("lat")
                        base_lon = event.get("lon")
                        health = 100.0
                        is_active = True
                        print(f"🎯 [SPAWN] Target TGT-1 spawned at {base_lat}, {base_lon}")

            # 2. Produce telemetry only if active
            if is_active:
                lat = base_lat + random.uniform(-0.0001, 0.0001)
                lon = base_lon + random.uniform(-0.0001, 0.0001)

                telemetry = TargetTelemetry(
                    target_id="TGT-1",
                    target_type="vehicle",
                    position=GeoPoint(lat=lat, lon=lon),
                    confidence=0.95 if health > 0 else 0.0,
                    timestamp=iso8601_utc_now()
                )

                producer.produce("target.raw", key="TGT-1", value=telemetry.model_dump_json())
                producer.poll(0)
            
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        consumer.close()


if __name__ == "__main__":
    main()
