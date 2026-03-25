# %% Imports
import argparse
import json
import math
import os
import random
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from confluent_kafka import Producer, Consumer
from pydantic import BaseModel

# %% Configuration
BASE_LAT = 31.800
BASE_LON = 35.100


# %% Data Contracts
class GeoPoint(BaseModel):
    lat: float
    lon: float
    alt: float


class DroneTelemetry(BaseModel):
    drone_id: str
    role: str
    position: GeoPoint
    velocity: float
    heading: float
    battery_percent: float
    flight_status: str
    assigned_target_id: Optional[str] = None
    timestamp: str


# %% Utils
def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# %% Drone Logic
class Drone:
    def __init__(self, drone_id: str, role: str, lat: float, lon: float, alt: float, flight_status: str = "SLEEP"):
        self.drone_id = drone_id
        self.role = role
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.battery = 100.0
        self.velocity = 5.0  # m/s
        self.heading = random.uniform(0, 360)
        self.target_lat = lat
        self.target_lon = lon
        self.target_alt = alt
        self.flight_status = flight_status
        self.weapons_count = 2 if role == "attack" else 0
        self.assigned_target_id: Optional[str] = None

    def update_waypoint(self, lat: float, lon: float, alt: float):
        self.target_lat = lat
        self.target_lon = lon
        self.target_alt = alt

    def wake_up(self, target_id: Optional[str] = None):
        if self.flight_status == "SLEEP":
            self.flight_status = "ACTIVE"
            self.assigned_target_id = target_id
            self.target_alt = 200.0 if self.role == "recon" else 100.0
            print(f"[SIM] {self.drone_id} WAKING UP. Target: {self.assigned_target_id}, Alt: {self.target_alt}")

    def tick(self, dt: float, battery_drain_per_sec: float):
        if self.flight_status == "SLEEP":
            return

        # Simple movement towards target
        step = 0.0001 * dt
        if abs(self.lat - self.target_lat) > step:
            if self.lat < self.target_lat:
                self.lat += step
            else:
                self.lat -= step

        if abs(self.lon - self.target_lon) > step:
            if self.lon < self.target_lon:
                self.lon += step
            else:
                self.lon -= step

        if abs(self.alt - self.target_alt) > step * 10:
            if self.alt < self.target_alt:
                self.alt += step * 10
            else:
                self.alt -= step * 10

        self.battery -= battery_drain_per_sec * dt
        if self.battery < 0:
            self.battery = 0

        self.heading = (self.heading + random.uniform(-5, 5)) % 360

        # RTB check
        if self.flight_status == "RETURNING":
            dist = math.sqrt((self.lat - BASE_LAT) ** 2 + (self.lon - BASE_LON) ** 2)
            if dist < 0.005:
                print(f"[SIM] {self.drone_id} arrived at base. Sleeping.")
                self.flight_status = "SLEEP"
                self.assigned_target_id = None
                self.alt = 0.0
                self.target_alt = 0.0

    def to_telemetry(self) -> DroneTelemetry:
        return DroneTelemetry(
            drone_id=self.drone_id,
            role=self.role,
            position=GeoPoint(lat=self.lat, lon=self.lon, alt=self.alt),
            velocity=self.velocity,
            heading=self.heading,
            battery_percent=round(self.battery, 1),
            flight_status=self.flight_status,
            assigned_target_id=self.assigned_target_id,
            timestamp=iso8601_utc_now()
        )


# %% Kafka Logic
def setup_kafka_clients(bootstrap_servers: str) -> tuple[Producer, Consumer]:
    producer = Producer({"bootstrap.servers": bootstrap_servers})
    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers,
        "group.id": f"drone-sim-{random.randint(0, 1000)}",
        "auto.offset.reset": "latest"
    })
    consumer.subscribe(["commands.drones", "commands.attack"])
    return producer, consumer


def process_drone_command(cmd_data: Dict[str, Any], topic: str, drones: List[Drone], producer: Producer):
    d_id = cmd_data.get("drone_id")
    for d in drones:
        if d.drone_id == d_id:
            if topic == "commands.drones":
                action = cmd_data.get("action")
                if action == "WAKE_UP":
                    d.wake_up(cmd_data.get("target_id"))
                elif action == "RECALL_DRONE":
                    print(f"[SIM] {d.drone_id} RECALL RECEIVED.")
                    d.flight_status = "RETURNING"
                    d.update_waypoint(BASE_LAT, BASE_LON, 0.0)
                elif action == "MANUAL_MOVE":
                    pos = cmd_data.get("position", {})
                    print(f"[SIM] {d.drone_id} MANUAL MOVE to {pos}")
                    d.flight_status = "MANUAL"
                    d.update_waypoint(pos.get("lat", d.lat), pos.get("lon", d.lon), pos.get("alt", d.alt))
                elif action == "RESUME_AUTO":
                    print(f"[SIM] {d.drone_id} RESUMING AUTO.")
                    d.flight_status = "ACTIVE"
                else:
                    pos = cmd_data.get("position", {})
                    d.update_waypoint(pos.get("lat", d.lat), pos.get("lon", d.lon), pos.get("alt", d.alt))

            elif topic == "commands.attack":
                if cmd_data.get("action") == "EXECUTE_STRIKE" and d.weapons_count > 0:
                    d.weapons_count -= 1
                    event = {
                        "drone_id": d.drone_id,
                        "target_id": cmd_data.get("target_id"),
                        "lat": d.lat,
                        "lon": d.lon,
                        "timestamp": iso8601_utc_now(),
                        "event": "PAYLOAD_DROPPED"
                    }
                    producer.produce("events.payload_dropped", key=d.drone_id, value=json.dumps(event))
                    print(f"!!! [ATTACK] {d.drone_id} executed strike on {cmd_data.get('target_id')}")


# %% Main Execution
def main():
    parser = argparse.ArgumentParser(description="Drone Swarm Simulator")
    parser.add_argument("--num-drones", type=int, default=20)
    parser.add_argument("--kafka-bootstrap", type=str,
                        default=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    args = parser.parse_args()

    producer, consumer = setup_kafka_clients(args.kafka_bootstrap)

    drones = []
    for i in range(args.num_drones):
        role = "recon" if i < 5 else "attack"
        drones.append(Drone(f"DRN-{i + 1}", role, BASE_LAT, BASE_LON, 0.0, "SLEEP"))

    print(f"[SIM] Running {len(drones)} drones. Connecting to {args.kafka_bootstrap}")

    try:
        while True:
            # 1. Consume commands
            msg = consumer.poll(0.01)
            if msg and not msg.error():
                cmd_data = json.loads(msg.value().decode("utf-8"))
                process_drone_command(cmd_data, msg.topic(), drones, producer)

            # 2. Update and Produce Telemetry
            for d in drones:
                d.tick(0.1, 0.05)
                telemetry = d.to_telemetry()
                producer.produce("telemetry.raw", key=d.drone_id, value=telemetry.model_dump_json())

            producer.poll(0)
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        consumer.close()


if __name__ == "__main__":
    main()
