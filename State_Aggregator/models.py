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
    model_config = ConfigDict(populate_by_name=True)

    drone_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    role: DroneRole
    position: GeoPoint
    velocity: float  # m/s
    heading: float  # degrees
    battery_percent: float = Field(ge=0, le=100)


class TargetType(str, Enum):
    VEHICLE = "vehicle"
    INFANTRY = "infantry"
    STRUCTURE = "structure"
    UNKNOWN = "unknown"


class TargetTelemetry(BaseModel):
    target_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    target_type: TargetType
    position: GeoPoint
    estimated_velocity: Optional[float] = None
    confidence: float = Field(ge=0, le=1)


class TargetPrediction(BaseModel):
    target_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    predicted_polygon: List[GeoPoint]
    time_horizon_sec: float


class WorldState(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    target_data: List[TargetTelemetry] = []
    recon_data: List[DroneTelemetry] = []
    attack_data: List[DroneTelemetry] = []
    predictions: List[TargetPrediction] = []


class CommandType(str, Enum):
    WAYPOINT = "waypoint"
    LOITER = "loiter"
    ATTACK = "attack"
    RETURN_TO_HOME = "rth"


class DroneCommand(BaseModel):
    drone_id: str
    command_type: CommandType
    params: Dict[str, float]
    priority: int = Field(default=1, ge=1, le=10)
