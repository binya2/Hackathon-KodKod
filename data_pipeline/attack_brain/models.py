from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

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

class TargetTelemetry(BaseModel):
    target_id: str
    timestamp: datetime
    target_type: str
    position: GeoPoint
    confidence: float

class DroneCommand(BaseModel):
    drone_id: str
    position: GeoPoint
