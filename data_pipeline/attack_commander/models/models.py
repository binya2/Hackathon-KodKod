from typing import Optional
from pydantic import BaseModel, Field


class RecallRequest(BaseModel):
    drone_id: str


class ManualMoveRequest(BaseModel):
    drone_id: str
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    alt: float


class ResumeAutoRequest(BaseModel):
    drone_id: str


class EngageRequest(BaseModel):
    action: str
    target_id: str
    drone_id: str


class DeployRequest(BaseModel):
    role: str
    target_id: Optional[str] = 'TGT-1'


class NewTargetRequest(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
