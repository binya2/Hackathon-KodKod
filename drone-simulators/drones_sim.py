import argparse
import json
import random
import time
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone

from confluent_kafka import Producer, Consumer, KafkaError


def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print(f"[KAFKA-PRODUCER] Delivery failed: {err}")
    else:
        print(f"[KAFKA-PRODUCER] Message delivered to {msg.topic()} [{msg.partition()}]")


@dataclass
class Drone:
    drone_id: str
    type: str  # recon | attack
    lat: float
    lon: float
    battery: float  # 0..100
    weapons_count: int = 0

    def tick(self, rng: random.Random, dt: float, move_deg: float, battery_drain_per_sec: float):
        self.lat += rng.uniform(-move_deg, move_deg)
        self.lon += rng.uniform(-move_deg, move_deg)
        self.battery -= battery_drain_per_sec * dt
        if self.battery < 0:
            self.battery = 0


def main():
    parser = argparse.ArgumentParser(description="Day 3: Drone Agents with Attack Execution")
    parser.add_argument("--num-drones", type=int, default=3)
    parser.add_argument("--tick-sec", type=float, default=0.75)
    parser.add_argument("--move-deg", type=float, default=0.0005)
    parser.add_argument("--battery-drain-per-sec", type=float, default=0.1)
    parser.add_argument(
        "--kafka-bootstrap",
        type=str,
        default=None,
        help="Kafka bootstrap server (default: localhost:9092 or env KAFKA_BOOTSTRAP_SERVERS).",
    )
    args = parser.parse_args()

    bootstrap = args.kafka_bootstrap or os.environ.get("KAFKA_BOOTSTRAP_SERVERS") or "localhost:9092"

    print(f"[SYSTEM] Starting Drone Sim... Connecting to {bootstrap}")
    
    # --- Kafka Producer Setup ---
    producer_conf = {
        "bootstrap.servers": bootstrap,
        "client.id": "drone-agent-producer",
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
        print("[ERROR] Could not connect to Kafka metadata.")
        sys.exit(1)

    # --- Kafka Consumer Setup ---
    consumer_conf = {
        "bootstrap.servers": bootstrap,
        "group.id": f"drone-agents-v{random.randint(1,1000)}", 
        "auto.offset.reset": "earliest", # Changed to earliest to catch missed commands
        "enable.auto.commit": True,
    }

    try:
        consumer = Consumer(consumer_conf)
        consumer.subscribe(["commands.attack"])
        print(f"[SYSTEM] Subscribed to commands.attack")
    except Exception as e:
        print(f"[ERROR] Consumer setup failed: {e}")
        sys.exit(1)

    rng = random.Random()
    base_lat, base_lon = 31.7000, 35.2000

    drones_map: dict[str, Drone] = {}
    for i in range(args.num_drones):
        d_id = f"DRN-{i+1}"
        d_type = "attack" if i < 2 else "recon"
        d_weapons = 2 if d_type == "attack" else 0
        d = Drone(d_id, d_type, base_lat + rng.uniform(-0.01, 0.01), base_lon + rng.uniform(-0.01, 0.01), 100.0, d_weapons)
        drones_map[d_id] = d
        print(f"[INIT] {d_id} ({d_type}) - Weapons: {d_weapons}")

    print(f"[SYSTEM] Simulation Loop Running.")

    try:
        while True:
            tick_start = time.time()

            # 1. Handle incoming attack commands
            msg = consumer.poll(0.1) # Wait up to 100ms for a command
            if msg is not None:
                if msg.error():
                    print(f"[KAFKA ERROR] Consumer error: {msg.error()}")
                else:
                    try:
                        raw_val = msg.value().decode("utf-8")
                        cmd = json.loads(raw_val)
                        drone_id = cmd.get("drone_id")
                        action = cmd.get("action")
                        
                        print(f"[CMD] Processing: {drone_id} -> {action}")

                        if drone_id in drones_map and action == "EXECUTE_STRIKE":
                            drone = drones_map[drone_id]
                            
                            if drone.weapons_count > 0:
                                drone.weapons_count -= 1
                                event = {
                                    "drone_id": drone.drone_id,
                                    "target_id": cmd.get("target_id", "TGT-1"),
                                    "lat": drone.lat,
                                    "lon": drone.lon,
                                    "timestamp": iso8601_utc_now(),
                                    "event": "PAYLOAD_DROPPED"
                                }
                                # Use callback for debugging
                                producer.produce(
                                    "events.payload_dropped", 
                                    key=drone.drone_id, 
                                    value=json.dumps(event),
                                    callback=delivery_report
                                )
                                # FORCE FLUSH to ensure message leaves immediately
                                producer.flush(1.0) 
                                print(f"!!! [ATTACK] {drone.drone_id} executed strike. Weapons left: {drone.weapons_count}")
                            else:
                                print(f"[IGNORE] {drone.drone_id} is OUT OF WEAPONS.")
                        else:
                            print(f"[DEBUG] No match for command (DroneID: {drone_id}, Action: {action})")
                    except Exception as e:
                        print(f"[WARN] Failed to process command: {e}")

            # 2. Update telemetry
            for drone in drones_map.values():
                drone.tick(rng, args.tick_sec, args.move_deg, args.battery_drain_per_sec)
                tel = {
                    "drone_id": drone.drone_id,
                    "type": drone.type,
                    "lat": drone.lat,
                    "lon": drone.lon,
                    "battery": int(round(drone.battery)),
                    "weapons_count": drone.weapons_count,
                    "timestamp": iso8601_utc_now()
                }
                producer.produce("telemetry.raw", key=drone.drone_id, value=json.dumps(tel))

            producer.poll(0)
            
            elapsed = time.time() - tick_start
            time.sleep(max(0, args.tick_sec - elapsed))

    except KeyboardInterrupt:
        print("[SYSTEM] Stopping.")
    finally:
        consumer.close()
        producer.flush()


if __name__ == "__main__":
    main()
