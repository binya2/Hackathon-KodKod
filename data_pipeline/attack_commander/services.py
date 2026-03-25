import json
import uuid
import httpx
from fastapi import HTTPException
from data_pipeline.attack_commander.kafka_client import (
    producer,
    delivery_report,
    log_to_kafka,
    iso8601_utc_now
)

STATE_AGGREGATOR_URL = "http://state_aggregator:8000/api/state"
TOPIC_COMMANDS = "commands.attack"
TOPIC_DEPLOYMENT = "commands.deployment"
TOPIC_INTEL = "events.intel"
TOPIC_DRONES = "commands.drones"


async def execute_engage(drone_id: str, target_id: str):
    state = await _fetch_current_state()
    target = next((t for t in state.get("target_data", []) if t["target_id"] == target_id), None)
    drone = next((d for d in state.get("recon_data", []) + state.get("attack_data", [])
                  if d["drone_id"] == drone_id), None)

    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found.")

    if drone.get("role", "").lower() != "attack":
        raise HTTPException(status_code=400, detail="Forbidden: Drone is not an attack drone.")

    if drone.get("weapons_count", 0) <= 0:
        raise HTTPException(status_code=400, detail="Forbidden: Drone has no ammunition.")

    # --- התוספת החדשה: חוסם תקיפה מרחפנים שישנים או חוזרים לבסיס ---
    if drone.get("flight_status") not in ["ACTIVE", "ATTACKING"]:
        raise HTTPException(status_code=400, detail=f"Forbidden: Drone is {drone.get('flight_status')}.")

    if drone.get("assigned_target_id") != target_id:
        raise HTTPException(status_code=400, detail="Forbidden: Drone is not assigned to this target.")
    # -----------------------------------------------------------

    payload = {
        "drone_id": drone_id,
        "action": "EXECUTE_STRIKE",
        "target_id": target_id,
        "timestamp": iso8601_utc_now()
    }
    
    if target:
        payload["position"] = target["position"]

    _produce_message(TOPIC_COMMANDS, drone_id, payload)
    return payload


async def execute_drone_deployment(role: str, target_id: str):
    payload = {
        "action": "DEPLOY_DRONE",
        "role": role,
        "target_id": target_id,
        "timestamp": iso8601_utc_now()
    }
    _produce_message(TOPIC_DEPLOYMENT, str(uuid.uuid4()), payload)
    return payload


async def spawn_target_with_swarm(lat: float, lon: float):
    state = await _fetch_current_state()
    _validate_available_resources(state)

    target_id = f"TGT-{str(uuid.uuid4())[:4].upper()}"
    intel_payload = {
        "action": "SPAWN_TARGET",
        "target_id": target_id,
        "lat": lat,
        "lon": lon,
        "timestamp": iso8601_utc_now()
    }

    _produce_message(TOPIC_INTEL, "", intel_payload)
    producer.poll(0)

    await _deploy_initial_swarm(target_id)

    log_to_kafka("INFO", f"Spawned target {target_id} and deployed swarm.")
    return target_id, intel_payload


async def execute_recall(drone_id: str):
    payload = {
        "drone_id": drone_id,
        "action": "RECALL_DRONE",
        "timestamp": iso8601_utc_now()
    }
    _produce_message(TOPIC_DRONES, drone_id, payload)
    return payload


async def execute_manual_move(drone_id: str, lat: float, lon: float, alt: float):
    payload = {
        "drone_id": drone_id,
        "action": "MANUAL_MOVE",
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "timestamp": iso8601_utc_now()
    }
    _produce_message(TOPIC_DRONES, drone_id, payload)
    return payload


async def execute_resume_auto(drone_id: str):
    payload = {
        "drone_id": drone_id,
        "action": "RESUME_AUTO",
        "timestamp": iso8601_utc_now()
    }
    _produce_message(TOPIC_DRONES, drone_id, payload)
    return payload


def _produce_message(topic: str, key: str, payload: dict):
    producer.produce(
        topic=topic,
        key=key,
        value=json.dumps(payload),
        callback=delivery_report
    )
    producer.poll(0)


async def _fetch_current_state():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(STATE_AGGREGATOR_URL, timeout=2.0)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            log_to_kafka("ERROR", f"State Aggregator unavailable: {exc}")
            raise HTTPException(status_code=503, detail="State Aggregator unavailable.")


def _validate_available_resources(state: dict):
    sleeping_recon = sum(1 for d in state.get("recon_data", []) if d.get("flight_status") == "SLEEP")
    sleeping_attack = sum(1 for d in state.get("attack_data", []) if d.get("flight_status") == "SLEEP")

    if sleeping_recon < 1 or sleeping_attack < 2:
        msg = f"Insufficient drones. Need 1 Recon (found {sleeping_recon}), 2 Attack (found {sleeping_attack})."
        log_to_kafka("WARN", msg)
        raise HTTPException(status_code=400, detail=msg)


async def _deploy_initial_swarm(target_id: str):
    deployments = [{"role": "recon"}, {"role": "attack"}, {"role": "attack"}]
    for dep in deployments:
        await execute_drone_deployment(dep["role"], target_id)
