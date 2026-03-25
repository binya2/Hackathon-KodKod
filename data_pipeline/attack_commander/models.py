from typing import Optional

from pydantic import BaseModel


# %% Data Contracts

class RecallRequest(BaseModel):
    drone_id: str


class ManualMoveRequest(BaseModel):
    drone_id: str
    lat: float
    lon: float
    alt: float


class ResumeAutoRequest(BaseModel):
    drone_id: str


class EngageRequest(BaseModel):
    action: str
    target_id: str
    drone_id: str


class DeployRequest(BaseModel):
    role: str  # recon or attack
    target_id: Optional[str] = "TGT-1"


class NewTargetRequest(BaseModel):
    lat: float
    lon: float
