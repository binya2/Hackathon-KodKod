import argparse
import json
import random
import time
import os
import sys
import math
from dataclasses import dataclass
from datetime import datetime, timezone

from confluent_kafka import Producer, Consumer, KafkaError


def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class Target:
    target_id: str
    lat: float
    lon: float
    health: float = 100.0
    status: str = "ACTIVE"

    def tick(self, rng: random.Random, dt: float, move_deg: float):
        if self.status == "DESTROYED":
            return
            
        # Move randomly if still active
        self.lat += rng.uniform(-move_deg, move_deg)
        self.lon += rng.uniform(-move_deg, move_deg)

    def apply_damage(self, drone_lat: float, drone_lon: float):
        if self.status == "DESTROYED":
            return 0

        # Calculate Euclidean distance
        dist = math.sqrt((self.lat - drone_lat)**2 + (self.lon - drone_lon)**2)
        
        # Hit detection: Max damage at distance 0, 0 damage at 0.05 deg (~5.5km)
        # Using a very large radius (0.05) to ensure hits occur during testing
        max_dist = 0.05 
        
        print(f"[DEBUG] Distance Calculation:")
        print(f"      Target: ({self.lat:.5f}, {self.lon:.5f})")
        print(f"      Drone:  ({drone_lat:.5f}, {drone_lon:.5f})")
        print(f"      Dist:   {dist:.6f} (Max to hit: {max_dist})")

        if dist < max_dist:
            # Damage is proportional to proximity
            damage = 50 * (1 - (dist / max_dist))
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                self.status = "DESTROYED"
            return damage
        return 0


def main():
    parser = argparse.ArgumentParser(description="Simulate a target with Health and Hit Detection.")
    parser.add_argument("--tick-sec", type=float, default=0.75)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--move-deg", type=float, default=0.0003)
    parser.add_argument(
        "--kafka-bootstrap",
        type=str,
        default=None,
        help="Kafka bootstrap server.",
    )
    args = parser.parse_args()

    bootstrap = args.kafka_bootstrap or os.environ.get("KAFKA_BOOTSTRAP_SERVERS") or "localhost:9092"
    rng = random.Random(args.seed)

    print(f"[TARGET] Connecting to {bootstrap}...")
    
    producer_conf = {"bootstrap.servers": bootstrap, "client.id": "target-sim-producer"}
    consumer_conf = {
        "bootstrap.servers": bootstrap,
        "group.id": f"target-hit-detector-{random.randint(1,9999)}",
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
    }

    try:
        producer = Producer(producer_conf)
        consumer = Consumer(consumer_conf)
        consumer.subscribe(["events.payload_dropped"])
        print(f"[TARGET] Monitoring events.payload_dropped")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # Initial position
    target = Target(target_id="TGT-1", lat=31.705, lon=35.205)
    
    print(f"[TARGET] Active at ({target.lat}, {target.lon})")

    try:
        while True:
            tick_start = time.time()

            msg = consumer.poll(0.0)
            if msg is not None and not msg.error():
                try:
                    event = json.loads(msg.value().decode("utf-8"))
                    drone_id = event.get("drone_id")
                    d_lat = event.get("lat")
                    d_lon = event.get("lon")
                    
                    damage = target.apply_damage(d_lat, d_lon)
                    if damage > 0:
                        print(f"💥 [HIT] By {drone_id}! Damage: {damage:.1f} | Health: {target.health:.1f}")
                        if target.status == "DESTROYED":
                            print(f"💀 [STATUS] TARGET DESTROYED!")
                    else:
                        print(f"[MISS] {drone_id} drop too far away.")
                except Exception as e:
                    print(f"[WARN] {e}")

            target.tick(rng, args.tick_sec, args.move_deg)

            state = {
                "target_id": target.target_id,
                "lat": target.lat,
                "lon": target.lon,
                "health": round(target.health, 1),
                "status": target.status,
                "timestamp": iso8601_utc_now(),
            }
            producer.produce("target.raw", key=target.target_id, value=json.dumps(state))
            producer.poll(0)

            time.sleep(max(0, args.tick_sec - (time.time() - tick_start)))

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.flush()

if __name__ == "__main__":
    main()
