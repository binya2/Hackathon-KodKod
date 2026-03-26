import logging
from typing import Dict, List, Optional

from data_pipeline.shared_models import DroneTelemetry, TargetTelemetry

logger = logging.getLogger(__name__)

_targets_registry: Dict[str, TargetTelemetry] = {}
_drones_registry: Dict[str, DroneTelemetry] = {}


def update_target(target: TargetTelemetry):
    """Adds or updates a target in the registry."""
    _targets_registry[target.target_id] = target


def get_target(target_id: str) -> Optional[TargetTelemetry]:
    """Retrieves a target from the registry by its ID."""
    return _targets_registry.get(target_id)


def get_active_targets() -> List[TargetTelemetry]:
    """Returns all targets with health > 0, excluding TGT-INIT."""
    return [t for t in _targets_registry.values() if t.health > 0 and t.target_id != "TGT-INIT"]


def update_drone_telemetry(telemetry: DroneTelemetry):
    """Adds or updates a drone's telemetry in the registry."""
    _drones_registry[telemetry.drone_id] = telemetry


def get_active_attack_drones() -> List[DroneTelemetry]:
    """Returns a list of all active attack drones."""
    return [
        d for d in _drones_registry.values()
        if d.role == "attack" and d.flight_status == "ACTIVE"
    ]


def get_sleeping_attack_drones() -> List[DroneTelemetry]:
    """Returns a list of all sleeping attack drones."""
    return [
        d for d in _drones_registry.values()
        if d.role == "attack" and d.flight_status == "SLEEP"
    ]


def get_drones_on_target(target_id: str) -> List[DroneTelemetry]:
    """Returns a list of active attack drones assigned to a specific target."""
    return [
        d for d in get_active_attack_drones()
        if d.assigned_target_id == target_id
    ]
