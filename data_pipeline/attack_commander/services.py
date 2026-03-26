import uuid
import math
import os
import json
import redis.asyncio as redis
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from data_pipeline.attack_commander.kafka_client import (
    produce_message,
    log_to_kafka,
    iso8601_utc_now
)

TOPIC_COMMANDS = "commands.attack"
TOPIC_DEPLOYMENT = "commands.deployment"
TOPIC_INTEL = "events.intel"
TOPIC_DRONES = "commands.drones"

# Initialize Redis client
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)


def _parse_redis_hash(redis_hash_data: dict) -> list:
    """Parses a Redis hash map (dict of JSON strings) into a list of dicts."""
    parsed_data = []
    for v in redis_hash_data.values():
        try:
            parsed_data.append(json.loads(v))
        except Exception:
            pass
    return parsed_data


async def _fetch_current_state():
    """Fetches targets and drones from Redis and formats them for the service."""
    targets_raw = await redis_client.hgetall("targets")
    drones_raw = await redis_client.hgetall("drones")

    target_data = _parse_redis_hash(targets_raw)
    all_drones = _parse_redis_hash(drones_raw)

    recon_data = [d for d in all_drones if d.get("role", "").lower() == "recon"]
    attack_data = [d for d in all_drones if d.get("role", "").lower() == "attack"]

    return {
        "target_data": target_data,
        "recon_data": recon_data,
        "attack_data": attack_data
    }


def _validate_target_for_engage(state: dict, target_id: str):
    target = next((t for t in state.get("target_data", []) if t["target_id"] == target_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Target {target_id} not found.")

    if target.get("health", 0) <= 0:
        raise HTTPException(status_code=400, detail=f"Forbidden: Target {target_id} is already destroyed.")
    return target


async def _validate_recon_for_engage(state: dict, target_id: str):
    target = next((t for t in state.get("target_data", []) if t["target_id"] == target_id), None)
    recons = state.get("recon_data", [])
    recon_ready = False
    for d in recons:
        if d.get("assigned_target_id") == target_id:
            # Explicit Redis refresh to get the most recent position directly
            recon_id = d["drone_id"]
            recon_json = await redis_client.hget("drones", recon_id)
            if recon_json:
                recon_data = json.loads(recon_json)
                
                # Add logical guard: check assigned_target_id in Redis
                if recon_data.get("assigned_target_id") != target_id:
                    raise HTTPException(status_code=400, detail="Recon drone not locked on target")

                # Check that flight status is ACTIVE or ATTACKING
                if recon_data.get("flight_status") in ["ACTIVE", "ATTACKING"]:
                    r_lat = recon_data["position"]["lat"]
                    r_lon = recon_data["position"]["lon"]
                    t_lat = target["position"]["lat"]
                    t_lon = target["position"]["lon"]
                    
                    # Use same distance formula as the test (meters)
                    dist_m = math.sqrt((r_lat - t_lat)**2 + (r_lon - t_lon)**2) * 111139
                    
                    # Log the calculated distance to Kafka for debugging
                    await log_to_kafka("DEBUG", f"Engage Check: Target {target_id}, Recon {recon_id}, Distance: {dist_m:.2f}m")

                    # Threshold: 50 meters. Strict limit.
                    if dist_m <= 50:
                        recon_ready = True
                        break

    if not recon_ready:
        await log_to_kafka("WARN", f"Blocked engage on {target_id} - Recon not in range.")
        raise HTTPException(status_code=400, detail="Forbidden: Cannot engage. Recon drone is deployed but hasn't arrived at the target yet.")


def _validate_attack_drone_for_engage(state: dict, target_id: str, drone_id: str):
    drone = next((d for d in state.get("recon_data", []) + state.get("attack_data", [])
                  if d["drone_id"] == drone_id), None)

    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found.")

    if drone.get("role", "").lower() != "attack":
        raise HTTPException(status_code=400, detail="Forbidden: Drone is not an attack drone.")

    if drone.get("weapons_count", 0) <= 0:
        raise HTTPException(status_code=400, detail="Forbidden: Drone has no ammunition.")

    if drone.get("flight_status") not in ["ACTIVE", "ATTACKING"]:
        raise HTTPException(status_code=400, detail=f"Forbidden: Drone is {drone.get('flight_status')}.")

    if drone.get("assigned_target_id") != target_id:
        raise HTTPException(status_code=400, detail="Forbidden: Drone is not assigned to this target.")


async def execute_engage(drone_id: str, target_id: str):
    state = await _fetch_current_state()

    target = _validate_target_for_engage(state, target_id)
    await _validate_recon_for_engage(state, target_id)
    _validate_attack_drone_for_engage(state, target_id, drone_id)

    payload = {
        "drone_id": drone_id,
        "action": "EXECUTE_STRIKE",
        "target_id": target_id,
        "position": target["position"],
        "timestamp": iso8601_utc_now()
    }

    await produce_message(TOPIC_DRONES, drone_id, payload)
    return payload


async def execute_drone_deployment(role: str, target_id: str):
    state = await _fetch_current_state()

    target = next((t for t in state.get("target_data", []) if t["target_id"] == target_id), None)
    if not target:
        await log_to_kafka("WARN", f"FAILED DEPLOYMENT: Target {target_id} not found.")
        raise HTTPException(status_code=404, detail=f"Target {target_id} not found. Deployment aborted.")

    payload = {
        "action": "DEPLOY_DRONE",
        "role": role,
        "target_id": target_id,
        "timestamp": iso8601_utc_now()
    }
    await produce_message(TOPIC_DEPLOYMENT, str(uuid.uuid4()), payload)
    return payload


async def spawn_target_with_swarm(lat: float, lon: float):
    state = await _fetch_current_state()
    await _validate_available_resources(state)

    target_id = f"TGT-{str(uuid.uuid4())[:4].upper()}"
    intel_payload = {
        "action": "SPAWN_TARGET",
        "target_id": target_id,
        "lat": lat,
        "lon": lon,
        "timestamp": iso8601_utc_now()
    }

    await produce_message("events.mission", "", intel_payload)
    await _deploy_initial_swarm(target_id, lat, lon)
    await log_to_kafka("INFO", f"Spawned target {target_id} and deployed swarm.")
    return target_id, intel_payload


async def execute_recall(drone_id: str):
    state = await _fetch_current_state()
    drone = next((d for d in state.get("recon_data", []) + state.get("attack_data", [])
                  if d["drone_id"] == drone_id), None)

    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found.")

    payload = {
        "drone_id": drone_id,
        "action": "RECALL_DRONE",
        "timestamp": iso8601_utc_now()
    }

    await produce_message(TOPIC_DRONES, drone_id, payload)
    return payload


async def execute_manual_move(drone_id: str, lat: float, lon: float, alt: float):
    state = await _fetch_current_state()
    drone = next((d for d in state.get("recon_data", []) + state.get("attack_data", [])
                  if d["drone_id"] == drone_id), None)

    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found.")

    payload = {
        "drone_id": drone_id,
        "action": "MANUAL_MOVE",
        "position": {"lat": lat, "lon": lon, "alt": alt},
        "timestamp": iso8601_utc_now()
    }

    await produce_message(TOPIC_DRONES, drone_id, payload)
    return payload


async def execute_resume_auto(drone_id: str):
    state = await _fetch_current_state()
    drone = next((d for d in state.get("recon_data", []) + state.get("attack_data", [])
                  if d["drone_id"] == drone_id), None)

    if not drone:
        raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found.")

    payload = {
        "drone_id": drone_id,
        "action": "RESUME_AUTO",
        "timestamp": iso8601_utc_now()
    }

    await produce_message(TOPIC_DRONES, drone_id, payload)
    return payload


async def _validate_available_resources(state: dict):
    sleeping_recon = sum(1 for d in state.get("recon_data", []) if d.get("flight_status") == "SLEEP")
    sleeping_attack = sum(1 for d in state.get("attack_data", []) if d.get("flight_status") == "SLEEP")

    if sleeping_recon < 1 or sleeping_attack < 2:
        msg = f"Insufficient drones. Need 1 Recon (found {sleeping_recon}), 2 Attack (found {sleeping_attack})."
        await log_to_kafka("WARN", msg)
        raise HTTPException(status_code=400, detail=msg)


async def _deploy_initial_swarm(target_id: str, lat: float, lon: float):
    deployments = [{"role": "recon"}, {"role": "attack"}, {"role": "attack"}]
    for dep in deployments:
        payload = {
            "action": "DEPLOY_DRONE",
            "role": dep["role"],
            "target_id": target_id,
            "position": {"lat": lat, "lon": lon},
            "timestamp": iso8601_utc_now()
        }
        await produce_message(TOPIC_DEPLOYMENT, str(uuid.uuid4()), payload)
