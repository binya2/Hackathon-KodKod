from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

# %% Models Definition

class DroneRole(str, Enum):
    RECON = "recon"
    ATTACK = "attack"
    RELAY = "relay"

class GeoPoint(BaseModel):
    lat: float
    lon: float
    alt: Optional[float] = None

class DroneTelemetry(BaseModel):
    drone_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    role: DroneRole
    position: GeoPoint
    velocity: float
    heading: float
    battery_percent: float

class TargetType(str, Enum):
    VEHICLE = "vehicle"
    INFANTRY = "infantry"
    STRUCTURE = "structure"

class TargetTelemetry(BaseModel):
    target_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    target_type: TargetType
    position: GeoPoint
    confidence: float

class WorldState(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    target_data: List[TargetTelemetry] = []
    recon_data: List[DroneTelemetry] = []
    attack_data: List[DroneTelemetry] = []
