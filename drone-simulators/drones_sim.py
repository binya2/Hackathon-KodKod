import argparse
import json
import random
import time
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from confluent_kafka import Producer, Consumer


def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class Drone:
    drone_id: str
    type: str  # recon | attack
    lat: float
    lon: float
    battery: float  # 0..100
    weapon_count: int = 0

    def tick(self, rng: random.Random, dt: float, move_deg: float, battery_drain_per_sec: float):
        # Very small random walk (good enough for Day 1 data flow proof)
        self.lat += rng.uniform(-move_deg, move_deg)
        self.lon += rng.uniform(-move_deg, move_deg)
        self.battery -= battery_drain_per_sec * dt
        if self.battery < 0:
            self.battery = 0


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def main():
    parser = argparse.ArgumentParser(description="Simulate multiple drones and publish telemetry to Kafka.")
    parser.add_argument("--num-drones", type=int, default=3)
    parser.add_argument("--tick-sec", type=float, default=0.75)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--kafka-bootstrap",
        type=str,
        default=None,
        help="Example: localhost:9092 (or set env KAFKA_BOOTSTRAP_SERVERS).",
    )

    # Optional: keep them inside a rectangle
    parser.add_argument("--min-lat", type=float, default=None)
    parser.add_argument("--max-lat", type=float, default=None)
    parser.add_argument("--min-lon", type=float, default=None)
    parser.add_argument("--max-lon", type=float, default=None)

    # Optional movement tuning
    parser.add_argument("--move-deg", type=float, default=0.0005)
    parser.add_argument("--battery-drain-per-sec", type=float, default=0.25)
    args = parser.parse_args()

    bootstrap = args.kafka_bootstrap or (  # noqa: E501
        os.environ.get("KAFKA_BOOTSTRAP_SERVERS") or "localhost:9092"
    )

    rng = random.Random(args.seed)

    base_lat = 31.7000
    base_lon = 35.2000

    drones: list[Drone] = []
    drones_map: dict[str, Drone] = {}
    
    for i in range(args.num_drones):
        drone_id = f"DRN-{i+1}"
        # Make the first few drones "attack" drones for testing
        drone_type = "attack" if i < 2 else "recon"
        # Initial weapon count for attack drones
        weapon_count = 2 if drone_type == "attack" else 0
        
        d = Drone(
            drone_id=drone_id,
            type=drone_type,
            lat=base_lat + rng.uniform(-0.01, 0.01),
            lon=base_lon + rng.uniform(-0.01, 0.01),
            battery=100.0,
            weapon_count=weapon_count
        )
        drones.append(d)
        drones_map[drone_id] = d

    # Kafka Producer
    producer = Producer({"bootstrap.servers": bootstrap, "client.id": "drones_sim"})
    
    # Kafka Consumer (for attack commands)
    consumer = Consumer({
        "bootstrap.servers": bootstrap,
        "group.id": f"drones_sim_group_{random.randint(0, 10000)}",
        "auto.offset.reset": "latest",
        "enable.auto.commit": True
    })
    consumer.subscribe(["commands.attack"])

    topic_telemetry = "telemetry.raw"
    topic_events = "events.attack"
    
    print(f"Drone Sim: Publishing telemetry to {topic_telemetry}")
    print(f"Drone Sim: Listening for commands on `commands.attack`")

    while True:
        tick_start = time.time()
        dt = args.tick_sec

        # 1. Check for Commands (Non-blocking poll)
        msg = consumer.poll(0.0)
        if msg is not None and not msg.error():
            try:
                cmd = json.loads(msg.value().decode("utf-8"))
                target_drone_id = cmd.get("drone_id")
                action = cmd.get("action")
                
                if action == "EXECUTE_STRIKE" and target_drone_id in drones_map:
                    drone = drones_map[target_drone_id]
                    if drone.weapon_count > 0:
                        drone.weapon_count -= 1
                        print(f"!!! [ATTACK] {drone.drone_id} executing strike. Weapons left: {drone.weapon_count}")
                        
                        # Emit Payload Dropped Event
                        event_payload = {
                            "drone_id": drone.drone_id,
                            "event": "PAYLOAD_DROPPED",
                            "lat": drone.lat,
                            "lon": drone.lon,
                            "timestamp": iso8601_utc_now()
                        }
                        producer.produce(topic=topic_events, key=drone.drone_id, value=json.dumps(event_payload))
                    else:
                        print(f"[ATTACK] {drone.drone_id} received EXECUTE_STRIKE but is OUT OF AMMO.")

            except Exception as e:
                print(f"Error processing command: {e}")

        # 2. Update Drones
        for drone in drones:
            drone.tick(
                rng=rng,
                dt=dt,
                move_deg=args.move_deg,
                battery_drain_per_sec=args.battery_drain_per_sec,
            )

            if (
                args.min_lat is not None
                and args.max_lat is not None
                and args.min_lon is not None
                and args.max_lon is not None
            ):
                drone.lat = clamp(drone.lat, args.min_lat, args.max_lat)
                drone.lon = clamp(drone.lon, args.min_lon, args.max_lon)

            battery_pct = int(round(drone.battery))

            msg = {
                "drone_id": drone.drone_id,
                "type": drone.type,
                "lat": drone.lat,
                "lon": drone.lon,
                "battery": battery_pct,
                "weapon_count": drone.weapon_count,
                "timestamp": iso8601_utc_now(),
            }

            producer.produce(topic=topic_telemetry, key=drone.drone_id, value=json.dumps(msg))
            producer.poll(0)

            # print(f"{drone.drone_id} | {drone.type} | battery: {battery_pct}% | weapons: {drone.weapon_count}")

        producer.flush(timeout=0)

        elapsed = time.time() - tick_start
        sleep_for = max(0.0, args.tick_sec - elapsed)
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
