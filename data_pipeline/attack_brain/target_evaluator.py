import json
import logging
from typing import List, Optional
from aiokafka import AIOKafkaProducer
from data_pipeline.shared.models import DroneTelemetry, TargetTelemetry

logger = logging.getLogger(__name__)

async def request_replacement(target: TargetTelemetry, producer: AIOKafkaProducer):
    """Requests a replacement drone for a target."""
    deploy_cmd = {
        "action": "DEPLOY_DRONE",
        "role": "attack",
        "target_id": target.target_id,
        "position": {"lat": target.position.lat, "lon": target.position.lon}
    }
    await producer.send_and_wait("commands.deployment", json.dumps(deploy_cmd).encode("utf-8"))

async def recall_drone(drone_id: str, producer: AIOKafkaProducer):
    """Sends a recall command for a specific drone."""
    recall_cmd = {"drone_id": drone_id, "action": "RECALL_DRONE"}
    await producer.send_and_wait("commands.drones", json.dumps(recall_cmd).encode("utf-8"))

async def evaluate_target_needs(target: TargetTelemetry, all_drones: List[DroneTelemetry], producer: AIOKafkaProducer):
    """Checks if a target has enough assigned drones and requests replacements if needed."""
    if target.target_id == "TGT-INIT":
        return

    assigned_count = sum(
        1 for d in all_drones
        if d.assigned_target_id == target.target_id and d.flight_status in ["ACTIVE", "ATTACKING", "EN_ROUTE"]
    )
    if assigned_count < 2:
        logger.info(f"[ASSIGN] Target {target.target_id} has {assigned_count} drones. Requesting replacement...")
        await request_replacement(target, producer)

def find_new_target(active_targets: List[TargetTelemetry], all_drones: List[DroneTelemetry]) -> Optional[TargetTelemetry]:
    """Finds an active target that needs more drones."""
    return next(
        (t for t in active_targets if sum(1 for d in all_drones if d.assigned_target_id == t.target_id) < 2), 
        None
    )
