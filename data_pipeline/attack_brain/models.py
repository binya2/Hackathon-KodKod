from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# %% Models Definition
class GeoPoint(BaseModel):
    lat: float
    lon: float
    alt: Optional[float] = None


class DroneTelemetry(BaseModel):
    drone_id: str
    timestamp: datetime
    role: str
    position: GeoPoint
    velocity: float
    heading: float
    battery_percent: float
    flight_status: str = "SLEEP"
    assigned_target_id: Optional[str] = None


class TargetTelemetry(BaseModel):
    target_id: str
    timestamp: datetime
    target_type: str
    position: GeoPoint
    confidence: float
    health: float = 100.0


class DroneCommand(BaseModel):
    drone_id: str
    position: GeoPoint
