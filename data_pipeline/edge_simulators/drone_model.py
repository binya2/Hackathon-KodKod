import math
import random
from datetime import datetime, timezone
from typing import Optional
from data_pipeline.shared_models import DroneTelemetry, GeoPoint

BASE_LAT = 31.800
BASE_LON = 35.100


class Drone:
    def __init__(self, drone_id: str, role: str, lat: float, lon: float, alt: float, flight_status: str = "SLEEP"):
        self.drone_id = drone_id
        self.role = role
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.battery = 100.0
        self.velocity = 5.0
        self.heading = random.uniform(0, 360)
        self.target_lat = lat
        self.target_lon = lon
        self.target_alt = alt
        self.flight_status = flight_status
        self.weapons_count = 5 if role == "attack" else 0
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
            print(f"[Drone] {self.drone_id} Waking up for target {self.assigned_target_id}")

    def recall(self):
        print(f"[Drone] {self.drone_id} recalling to base.")
        self.flight_status = "RETURNING"
        self.assigned_target_id = None
        self.update_waypoint(BASE_LAT, BASE_LON, 0.0)

    def manual_move(self, lat: float, lon: float, alt: float):
        print(f"[Drone] {self.drone_id} manual move to {lat}, {lon}, {alt}")
        self.flight_status = "MANUAL"
        self.assigned_target_id = None
        self.update_waypoint(lat, lon, alt)

    def tick(self, dt: float):
        if self.flight_status == "SLEEP":
            self._handle_charging_and_reloading(dt)
            return

        self._handle_movement(dt)
        self._check_battery_and_crash(dt)
        self._check_arrival_at_base()

        return self._check_strike_condition()

    def _check_strike_condition(self) -> Optional[dict]:
        if self.flight_status != "ATTACKING" or not self.assigned_target_id:
            return None

        # Calculate horizontal distance (lat/lon)
        dist = math.sqrt((self.lat - self.target_lat) ** 2 + (self.lon - self.target_lon) ** 2)

        # RELEASE ON CONTACT (10 meters = 0.0001 degrees)
        if dist < 0.0001 and self.weapons_count > 0:
            self.weapons_count -= 1
            print(
                f"💥 [STRIKE] {self.drone_id} RELEASED PAYLOAD on {self.assigned_target_id}! Ammo: {self.weapons_count}")

            # Return to ACTIVE mode to wait for next explicit command
            self.flight_status = "ACTIVE"

            return {
                "drone_id": self.drone_id,
                "target_id": self.assigned_target_id,
                "lat": self.lat,
                "lon": self.lon,
                "event": "PAYLOAD_DROPPED"
            }

        return None

    def _handle_movement(self, dt: float):
        # Calculate current distance to target
        dist = math.sqrt((self.lat - self.target_lat) ** 2 + (self.lon - self.target_lon) ** 2)

        # Base speed: 0.00025 deg/sec is approx 27 m/s (100 km/h)
        base_speed = 0.00025
        speed_multiplier = 1.0

        if self.flight_status == "RETURNING":
            speed_multiplier = 1.5
        elif self.flight_status == "ATTACKING":
            if dist > 0.001:  # Far from target (>110m)
                speed_multiplier = 3.0  # Sprint to close the gap
            elif dist > 0.0002:  # Getting closer (20m - 110m)
                speed_multiplier = 2.0  # Fast approach
            else:  # Very close (<20m)
                speed_multiplier = 1.2  # Precision match

        step = base_speed * dt * speed_multiplier

        # Calculate direction vector
        delta_lat = self.target_lat - self.lat
        delta_lon = self.target_lon - self.lon

        if dist > 0:
            # Move towards target proportional to the distance in each axis
            self.lat += (delta_lat / dist) * step
            self.lon += (delta_lon / dist) * step

        # Altitude movement with snap (much faster)
        alt_step = 50.0 * dt
        if abs(self.alt - self.target_alt) <= alt_step:
            self.alt = self.target_alt
        else:
            self.alt += alt_step if self.alt < self.target_alt else -alt_step

        if dist > 0:
            self.heading = math.degrees(math.atan2(delta_lon, delta_lat)) % 360

    def _handle_charging_and_reloading(self, dt: float):
        if self.battery < 100.0:
            self.battery = min(100.0, self.battery + (5.0 * dt))
        if self.role == "attack" and self.weapons_count < 5:
            # Chance to reload one grenade per tick if in SLEEP
            if random.random() < (0.5 * dt):
                self.weapons_count += 1

    def _check_battery_and_crash(self, dt: float):
        battery_drain = 0.05 * dt
        self.battery -= battery_drain

        # AUTO-RECALL on low battery (20%)
        if self.battery < 20.0 and self.flight_status not in ["RETURNING", "SLEEP", "CRASHED"]:
            print(f"🪫 [Drone] {self.drone_id} Low battery ({self.battery:.1f}%). Recalling...")
            self.recall()

        if self.battery <= 0:
            self.battery = 0
            self.flight_status = "CRASHED"
            if self.alt > 0:
                self.alt = max(0.0, self.alt - 0.002)

    def _check_arrival_at_base(self):
        if self.flight_status == "RETURNING":
            dist = math.sqrt((self.lat - BASE_LAT) ** 2 + (self.lon - BASE_LON) ** 2)
            # 0.0001 degrees is approx 11 meters
            if dist < 0.0001 and self.alt <= 0.1:
                self.flight_status = "SLEEP"
                self.assigned_target_id = None
                self.lat, self.lon, self.alt = BASE_LAT, BASE_LON, 0.0
                self.target_alt = 0.0
                print(f"🏠 [Drone] {self.drone_id} landed and entered SLEEP mode.")

    def to_telemetry(self) -> DroneTelemetry:
        return DroneTelemetry(
            drone_id=self.drone_id,
            role=self.role,
            position=GeoPoint(lat=self.lat, lon=self.lon, alt=self.alt),
            velocity=self.velocity,
            heading=self.heading,
            battery_percent=round(self.battery, 1),
            weapons_count=self.weapons_count,
            flight_status=self.flight_status,
            assigned_target_id=self.assigned_target_id
        )
