# %% Imports
import argparse
import json
import random
import time
import os
import sys
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from confluent_kafka import Producer, Consumer

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

    def update_waypoint(self, lat, lon, alt):
        self.target_lat = lat
        self.target_lon = lon
        self.target_alt = alt

    def wake_up(self):
        if self.flight_status == "SLEEP":
            self.flight_status = "ACTIVE"
            self.target_alt = 200.0 if self.role == "recon" else 100.0
            print(f"[SIM] {self.drone_id} WAKING UP. Target Alt: {self.target_alt}")

    def tick(self, dt: float, battery_drain_per_sec: float):
        if self.flight_status == "SLEEP":
            return

        # Simple movement towards target
        step = 0.0001 * dt
        if abs(self.lat - self.target_lat) > step:
            if self.lat < self.target_lat: self.lat += step
            else: self.lat -= step
        
        if abs(self.lon - self.target_lon) > step:
            if self.lon < self.target_lon: self.lon += step
            else: self.lon -= step
        
        if abs(self.alt - self.target_alt) > step * 10:
            if self.alt < self.target_alt: self.alt += step * 10
            else: self.alt -= step * 10

        self.battery -= battery_drain_per_sec * dt
        if self.battery < 0: self.battery = 0
        
        self.heading = (self.heading + random.uniform(-5, 5)) % 360

    def to_telemetry(self) -> DroneTelemetry:
        return DroneTelemetry(
            drone_id=self.drone_id,
            role=self.role,
            position=GeoPoint(lat=self.lat, lon=self.lon, alt=self.alt),
            velocity=self.velocity,
            heading=self.heading,
            battery_percent=round(self.battery, 1),
            flight_status=self.flight_status,
            timestamp=iso8601_utc_now()
        )

# %% Main Execution
def main():
    parser = argparse.ArgumentParser(description="Drone Swarm Simulator")
    parser.add_argument("--num-drones", type=int, default=20)
    parser.add_argument("--kafka-bootstrap", type=str, default=os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    args = parser.parse_args()

    producer = Producer({"bootstrap.servers": args.kafka_bootstrap})
    consumer = Consumer({
        "bootstrap.servers": args.kafka_bootstrap,
        "group.id": f"drone-sim-{random.randint(0, 1000)}",
        "auto.offset.reset": "latest"
    })
    consumer.subscribe(["commands.drones", "commands.attack"])

    drones = []
    for i in range(args.num_drones):
        role = "recon" if i < 5 else "attack"
        # All drones start in SLEEP mode at 0.0 altitude
        status = "SLEEP"
        initial_alt = 0.0
            
        drones.append(Drone(f"DRN-{i+1}", role, BASE_LAT, BASE_LON, initial_alt, status))

    print(f"[SIM] Running {len(drones)} drones. Connecting to {args.kafka_bootstrap}")

    try:
        while True:
            # 1. Consume commands
            msg = consumer.poll(0.01)
            if msg and not msg.error():
                cmd = json.loads(msg.value().decode("utf-8"))
                d_id = cmd.get("drone_id")
                
                for d in drones:
                    if d.drone_id == d_id:
                        if msg.topic() == "commands.drones":
                            action = cmd.get("action")
                            if action == "WAKE_UP":
                                d.wake_up()
                            else:
                                pos = cmd.get("position", {})
                                d.update_waypoint(pos.get("lat", d.lat), pos.get("lon", d.lon), pos.get("alt", d.alt))
                        
                        elif msg.topic() == "commands.attack":
                            if cmd.get("action") == "EXECUTE_STRIKE" and d.weapons_count > 0:
                                d.weapons_count -= 1
                                event = {
                                    "drone_id": d.drone_id,
                                    "target_id": cmd.get("target_id"),
                                    "lat": d.lat,
                                    "lon": d.lon,
                                    "timestamp": iso8601_utc_now(),
                                    "event": "PAYLOAD_DROPPED"
                                }
                                producer.produce("events.payload_dropped", key=d.drone_id, value=json.dumps(event))
                                print(f"!!! [ATTACK] {d.drone_id} executed strike on {cmd.get('target_id')}")

            # 2. Update and Produce Telemetry
            for d in drones:
                d.tick(0.5, 0.05)
                telemetry = d.to_telemetry()
                producer.produce("telemetry.raw", key=d.drone_id, value=telemetry.model_dump_json())
            
            producer.poll(0)
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        consumer.close()

if __name__ == "__main__":
    main()
