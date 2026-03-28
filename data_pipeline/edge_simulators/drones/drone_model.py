import math
import random
from datetime import datetime, timezone
from typing import Optional
from data_pipeline.shared.models import DroneTelemetry, GeoPoint

BASE_LAT = 31.8
BASE_LON = 35.1


class Drone:

    def __init__(self, drone_id: str, role: str, lat: float, lon: float, alt: float, flight_status: str = 'SLEEP'):
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
        self.weapons_count = 5 if role == 'attack' else 0
        self.assigned_target_id: Optional[str] = None
        self.timestamp = datetime.now(timezone.utc)

    def update_waypoint(self, lat: float, lon: float, alt: float):
        self.target_lat = lat
        self.target_lon = lon
        self.target_alt = alt

    def wake_up(self, target_id: Optional[str] = None, target_lat: Optional[float] = None,
                target_lon: Optional[float] = None):
        if self.flight_status == 'SLEEP':
            self.flight_status = 'EN_ROUTE'
            self.assigned_target_id = target_id
            self.target_alt = 200.0 if self.role == 'recon' else 100.0
            if target_lat is not None and target_lon is not None:
                self.target_lat = target_lat
                self.target_lon = target_lon
            self.timestamp = datetime.now(timezone.utc)

            print(
                f'[Drone] {self.drone_id} En route to target {self.assigned_target_id} at ({target_lat}, {target_lon})')

    def recall(self):
        print(f'[Drone] {self.drone_id} recalling to base.')
        self.flight_status = 'RETURNING'
        self.assigned_target_id = None
        self.timestamp = datetime.now(timezone.utc)
        self.update_waypoint(BASE_LAT, BASE_LON, 0.0)

    def manual_move(self, lat: float, lon: float, alt: float):
        print(f'[Drone] {self.drone_id} manual move to {lat}, {lon}, {alt}')
        self.flight_status = 'MANUAL'
        # self.assigned_target_id = None
        self.timestamp = datetime.now(timezone.utc)
        self.update_waypoint(lat, lon, alt)

    def tick(self, dt: float):
        self.timestamp = datetime.now(timezone.utc)
        if self.flight_status == 'SLEEP':
            self._handle_charging_and_reloading(dt)
            return
        self._handle_movement(dt)
        self._check_battery_and_crash(dt)
        self._check_arrival_at_base()
        return self._check_strike_condition()

    def _check_arrival_at_target(self):
        pass

    def _check_strike_condition(self) -> Optional[dict]:
        if self.flight_status != 'ATTACKING' or not self.assigned_target_id:
            return None
        dist = math.sqrt((self.lat - self.target_lat) ** 2 + (self.lon - self.target_lon) ** 2)
        if dist < 0.0001 and self.weapons_count > 0:
            self.weapons_count -= 1
            print(
                f'💥 [STRIKE] {self.drone_id} RELEASED PAYLOAD on {self.assigned_target_id}! Ammo: {self.weapons_count}')
            self.flight_status = 'ACTIVE'
            return {'drone_id': self.drone_id, 'target_id': self.assigned_target_id, 'lat': self.lat, 'lon': self.lon,
                    'event': 'PAYLOAD_DROPPED'}
        return None

    def _handle_movement(self, dt: float):
        dist = math.sqrt((self.lat - self.target_lat) ** 2 + (self.lon - self.target_lon) ** 2)
        speed_multiplier = self._get_speed_multiplier(dist)
        base_speed = 0.00025
        step = base_speed * dt * speed_multiplier
        if dist > 0 and step > 0:
            self._calculate_next_position(step, dist)
        self._update_altitude(dt)

    def _get_speed_multiplier(self, dist: float) -> float:
        if self.flight_status == 'MANUAL':
            return 1.0
        if self.flight_status == 'EN_ROUTE':
            return 1.0
        if self.flight_status == 'RETURNING':
            return 1.5
        if self.flight_status == 'ATTACKING':
            if dist > 0.001:
                return 3.0
            if dist > 0.0002:
                return 2.0
            return 1.2
        return 0.0

    def _calculate_next_position(self, step: float, dist: float):
        actual_step = min(step, dist)
        delta_lat = self.target_lat - self.lat
        delta_lon = self.target_lon - self.lon
        bearing = math.atan2(delta_lon, delta_lat)
        self.lat += math.cos(bearing) * actual_step
        self.lon += math.sin(bearing) * actual_step
        self.heading = math.degrees(bearing) % 360

    def _update_altitude(self, dt: float):
        alt_step = 50.0 * dt
        if abs(self.alt - self.target_alt) <= alt_step:
            self.alt = self.target_alt
        else:
            self.alt += alt_step if self.alt < self.target_alt else -alt_step

    def _handle_charging_and_reloading(self, dt: float):
        if self.battery < 100.0:
            self.battery = min(100.0, self.battery + 5.0 * dt)
        if self.role == 'attack' and self.weapons_count < 5:
            if random.random() < 0.5 * dt:
                self.weapons_count += 1

    def _check_battery_and_crash(self, dt: float):
        battery_drain = 0.05 * dt
        self.battery -= battery_drain
        if self.battery < 20.0 and self.flight_status not in ['RETURNING', 'SLEEP', 'CRASHED']:
            print(f'🪫 [Drone] {self.drone_id} Low battery ({self.battery:.1f}%). Recalling...')
            self.recall()
        if self.battery <= 0:
            self.battery = 0
            self.flight_status = 'CRASHED'
            self.target_alt = 0.0

    def _check_arrival_at_base(self):
        if self.flight_status == 'RETURNING':
            dist = math.sqrt((self.lat - BASE_LAT) ** 2 + (self.lon - BASE_LON) ** 2)
            if dist < 0.0001 and self.alt <= 0.1:
                self.flight_status = 'SLEEP'
                self.assigned_target_id = None
                self.lat, self.lon, self.alt = (BASE_LAT, BASE_LON, 0.0)
                self.target_alt = 0.0
                print(f'🏠 [Drone] {self.drone_id} landed and entered SLEEP mode.')

    def to_telemetry(self) -> DroneTelemetry:
        return DroneTelemetry(drone_id=self.drone_id, timestamp=self.timestamp, role=self.role,
                              position=GeoPoint(lat=self.lat, lon=self.lon, alt=self.alt), velocity=self.velocity,
                              heading=self.heading, battery_percent=round(self.battery, 1),
                              weapons_count=self.weapons_count, flight_status=self.flight_status,
                              assigned_target_id=self.assigned_target_id)
