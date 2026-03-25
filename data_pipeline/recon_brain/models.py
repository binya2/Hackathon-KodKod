from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# %% Models Definition (Decoupled Copy)
class GeoPoint(BaseModel):
    lat: float
    lon: float
    alt: Optional[float] = None


class TargetType(str, Enum):
    VEHICLE = "vehicle"
    INFANTRY = "infantry"
    STRUCTURE = "structure"


class TargetTelemetry(BaseModel):
    target_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_type: TargetType
    position: GeoPoint
    confidence: float
    health: float = 100.0


class DroneTelemetry(BaseModel):
    drone_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    role: str
    position: GeoPoint
    velocity: float
    heading: float
    battery_percent: float
    flight_status: str = "SLEEP"
    assigned_target_id: Optional[str] = None


class NavigationCommand(BaseModel):
    drone_id: str
    position: GeoPoint
    priority: int = 1
