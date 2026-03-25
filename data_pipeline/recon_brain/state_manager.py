import logging
from typing import Dict, List

from data_pipeline.shared_models import DroneTelemetry

logger = logging.getLogger(__name__)

_drones_registry: Dict[str, DroneTelemetry] = {}


def update_drone_telemetry(telemetry: DroneTelemetry):
    """Updates the registry with new drone telemetry."""
    _drones_registry[telemetry.drone_id] = telemetry


def get_active_recon_drones() -> List[DroneTelemetry]:
    """Returns a list of active recon drones."""
    active = [d for d in _drones_registry.values() if d.role.lower() == "recon" and d.flight_status == "ACTIVE"]
    return active


def get_sleeping_recon_drones() -> List[DroneTelemetry]:
    """Returns a list of sleeping recon drones."""
    sleeping = [d for d in _drones_registry.values() if d.role.lower() == "recon" and d.flight_status == "SLEEP"]
    if not sleeping and not _drones_registry:
        logger.warning("Recon Brain registry is EMPTY. No telemetry received yet?")
    return sleeping


def get_active_recon_drone_for_target(target_id: str) -> List[DroneTelemetry]:
    """Returns a list of active recon drones assigned to a specific target."""
    return [d for d in get_active_recon_drones() if d.assigned_target_id == target_id]
