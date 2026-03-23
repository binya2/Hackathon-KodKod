from __future__ import annotations

from datetime import datetime
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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    target_type: TargetType
    position: GeoPoint
    confidence: float


class NavigationCommand(BaseModel):
    drone_id: str
    target_lat: float
    target_lon: float
    target_alt: float
    priority: int = 1
