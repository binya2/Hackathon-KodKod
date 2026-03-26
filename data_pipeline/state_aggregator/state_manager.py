import logging
from datetime import datetime, timezone
from typing import Dict

from data_pipeline.shared_models import WorldState, DroneTelemetry, TargetTelemetry, DroneRole

logger = logging.getLogger(__name__)

_global_state = WorldState()
_drones_registry: Dict[str, DroneTelemetry] = {}
_targets_registry: Dict[str, TargetTelemetry] = {}


def update_drone_telemetry(telemetry: DroneTelemetry):
    """Updates the registry with new drone telemetry."""
    _drones_registry[telemetry.drone_id] = telemetry


def update_target_telemetry(telemetry: TargetTelemetry):
    """Updates the registry with new target telemetry."""
    _targets_registry[telemetry.target_id] = telemetry


def garbage_collect_stale_drones():
    """Removes drones that have not sent telemetry for a while."""
    now = datetime.now(timezone.utc)
    # Increased to 15s for more stability during startup
    stale_drones = [
        d_id for d_id, drone in _drones_registry.items()
        if (now - drone.timestamp).total_seconds() > 15.0
    ]
    for d_id in stale_drones:
        logger.warning(f"Removing stale drone %s from state (no telemetry for >15s)", d_id)
        del _drones_registry[d_id]


def _update_global_state():
    now = datetime.now(timezone.utc)
    _global_state.timestamp = now

    # Thread-safe local copies
    drones = list(_drones_registry.values())
    targets = list(_targets_registry.values())

    # Use lowercase comparison for robustness
    _global_state.recon_data = sorted(
        [d for d in drones if d.role.lower() == "recon"],
        key=lambda x: 0 if x.flight_status == "ACTIVE" else 1
    )

    _global_state.attack_data = sorted(
        [d for d in drones if d.role.lower() == "attack"],
        key=lambda x: 0 if x.flight_status == "ACTIVE" else 1
    )

    _global_state.target_data = [t for t in targets if t.health > 0]


def get_world_state() -> WorldState:
    """Constructs and returns the current world state from the registries."""
    garbage_collect_stale_drones()
    _update_global_state()
    return _global_state
