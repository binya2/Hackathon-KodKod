from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


# %% Enums Definition

class DroneRole(str, Enum):
    RECON = "recon"
    ATTACK = "attack"
    RELAY = "relay"


class TargetType(str, Enum):
    VEHICLE = "vehicle"
    INFANTRY = "infantry"
    STRUCTURE = "structure"


# %% Base Models Definition

class GeoPoint(BaseModel):
    lat: float
    lon: float
    alt: Optional[float] = None


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


class TargetTelemetry(BaseModel):
    target_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_type: str = "vehicle"
    position: GeoPoint
    confidence: float
    health: float = 100.0


# %% Command Models

class NavigationCommand(BaseModel):
    drone_id: str
    position: GeoPoint
    priority: int = 1


class DroneCommand(BaseModel):
    drone_id: str
    position: GeoPoint


# %% State Aggregator Models

class WorldState(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_data: List[TargetTelemetry] = []
    recon_data: List[DroneTelemetry] = []
    attack_data: List[DroneTelemetry] = []
