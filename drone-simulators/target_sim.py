import argparse
import json
import random
import time
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone

from confluent_kafka import Producer


def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class Target:
    target_id: str
    lat: float
    lon: float

    def tick(self, rng: random.Random, dt: float, move_deg: float):
        self.lat += rng.uniform(-move_deg, move_deg)
        self.lon += rng.uniform(-move_deg, move_deg)


def main():
    parser = argparse.ArgumentParser(description="Simulate a target and publish its position to Kafka.")
    parser.add_argument("--tick-sec", type=float, default=0.75)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--kafka-bootstrap",
        type=str,
        default=None,
        help="Example: localhost:9092 or env KAFKA_BOOTSTRAP_SERVERS.",
    )
    parser.add_argument("--move-deg", type=float, default=0.0003)
    args = parser.parse_args()

    bootstrap = args.kafka_bootstrap or os.environ.get("KAFKA_BOOTSTRAP_SERVERS") or "localhost:9092"
    rng = random.Random(args.seed)

    print(f"[TARGET] Connecting to Kafka at {bootstrap}...")
    
    producer_conf = {
        "bootstrap.servers": bootstrap, 
        "client.id": "target_sim",
        "allow.auto.create.topics": "true"
    }
    
    producer = None
    for i in range(10):
        try:
            producer = Producer(producer_conf)
            producer.list_topics(timeout=5)
            break
        except Exception as e:
            print(f"[RETRY {i+1}/10] Waiting for Kafka metadata... {e}")
            time.sleep(3)
    
    if not producer:
        sys.exit(1)

    # Starting position for the target
    target = Target(target_id="TGT-1", lat=31.78, lon=35.22)
    topic = "target.raw"

    print(f"[TARGET] Simulation started.")

    try:
        while True:
            tick_start = time.time()
            target.tick(rng=rng, dt=args.tick_sec, move_deg=args.move_deg)

            msg = {
                "target_id": target.target_id,
                "lat": target.lat,
                "lon": target.lon,
                "timestamp": iso8601_utc_now(),
            }

            producer.produce(topic=topic, key=target.target_id, value=json.dumps(msg))
            producer.poll(0)

            elapsed = time.time() - tick_start
            sleep_for = max(0.0, args.tick_sec - elapsed)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()


if __name__ == "__main__":
    main()
