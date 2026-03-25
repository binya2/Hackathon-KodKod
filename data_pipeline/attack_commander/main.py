import json
import uuid

import httpx
from fastapi import FastAPI, HTTPException

from kafka_client import producer, delivery_report, log_to_kafka, iso8601_utc_now
from models import (
    EngageRequest, DeployRequest, NewTargetRequest,
    RecallRequest, ManualMoveRequest, ResumeAutoRequest
)

# --- App Initialization ---
app = FastAPI(title="Attack Commander Service")

# --- Constants ---
TOPIC_COMMANDS = "commands.attack"
TOPIC_DEPLOYMENT = "commands.deployment"
TOPIC_INTEL = "events.intel"
TOPIC_DRONES = "commands.drones"
STATE_AGGREGATOR_URL = "http://state_aggregator:8000/api/state"


# --- Endpoints ---
# %% API Endpoints

@app.post("/engage")
async def engage(req: EngageRequest):
    try:
        print(f"[API] Engage: {req.drone_id} vs {req.target_id}")

        if req.action != "engage":
            raise HTTPException(status_code=400, detail="Invalid action.")

        payload = {
            "drone_id": req.drone_id,
            "action": "EXECUTE_STRIKE",
            "target_id": req.target_id,
            "timestamp": iso8601_utc_now()
        }

        producer.produce(
            topic=TOPIC_COMMANDS,
            key=req.drone_id,
            value=json.dumps(payload),
            callback=delivery_report
        )
        producer.flush(1.0)
        return {"status": "command_sent", "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        log_to_kafka("ERROR", f"Engage failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Check system logs.")


@app.post("/deploy_drone")
async def deploy_drone(req: DeployRequest):
    try:
        if req.role not in ["recon", "attack"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'recon' or 'attack'.")

        payload = {
            "action": "DEPLOY_DRONE",
            "role": req.role,
            "target_id": req.target_id,
            "timestamp": iso8601_utc_now()
        }

        key = str(uuid.uuid4())
        producer.produce(
            topic=TOPIC_DEPLOYMENT,
            key=key,
            value=json.dumps(payload),
            callback=delivery_report
        )
        producer.flush(1.0)
        return {"status": "deployment_request_sent", "payload": payload}
    except HTTPException:
        raise
    except Exception as e:
        log_to_kafka("ERROR", f"Deploy failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Check system logs.")


@app.post("/new_target")
async def new_target(req: NewTargetRequest):
    """
    Creates a new target and auto-scrambles the first recon drone in one call.
    Includes Pre-Deployment Resource Validation.
    """
    try:
        # 1. Pre-Deployment Resource Validation
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(STATE_AGGREGATOR_URL, timeout=2.0)
                response.raise_for_status()
                state = response.json()
            except Exception as exc:
                log_to_kafka("ERROR", f"Failed to fetch state from aggregator: {exc}")
                raise HTTPException(status_code=503, detail="State Aggregator unavailable.")

        sleeping_recon = sum(1 for d in state.get("recon_data", []) if d.get("flight_status") == "SLEEP")
        sleeping_attack = sum(1 for d in state.get("attack_data", []) if d.get("flight_status") == "SLEEP")

        if sleeping_recon < 1 or sleeping_attack < 2:
            msg = (f"Insufficient sleeping drones available. Found Recon: {sleeping_recon}, "
                   f"Attack: {sleeping_attack}. Required: 1 Recon, 2 Attack.")
            log_to_kafka("WARN", msg)
            raise HTTPException(status_code=400, detail=msg)

        # 2. Implementation
        target_id = f"TGT-{str(uuid.uuid4())[:4].upper()}"
        intel_payload = {
            "action": "SPAWN_TARGET",
            "lat": req.lat,
            "lon": req.lon,
            "timestamp": iso8601_utc_now()
        }

        # Produce SPAWN_TARGET
        producer.produce(
            topic=TOPIC_INTEL,
            value=json.dumps(intel_payload),
            callback=delivery_report
        )

        # Produce 3 DEPLOY_DRONE messages (1 recon, 2 attack)
        deployments = [{"role": "recon"}, {"role": "attack"}, {"role": "attack"}]
        for dep in deployments:
            deploy_payload = {
                "action": "DEPLOY_DRONE",
                "role": dep["role"],
                "target_id": target_id,
                "timestamp": iso8601_utc_now()
            }
            key = str(uuid.uuid4())
            producer.produce(
                topic=TOPIC_DEPLOYMENT,
                key=key,
                value=json.dumps(deploy_payload),
                callback=delivery_report
            )

        producer.flush(1.0)
        log_to_kafka("INFO", f"Successfully spawned target {target_id} and deployed swarm.")
        return {
            "status": "target_spawned_and_swarm_deployed",
            "target_id": target_id,
            "intel_payload": intel_payload,
            "deployment_count": len(deployments)
        }
    except HTTPException:
        raise
    except Exception as e:
        log_to_kafka("ERROR", f"New target creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Check system logs.")


@app.post("/recall_drone")
async def recall_drone(req: RecallRequest):
    payload = {
        "drone_id": req.drone_id,
        "action": "RECALL_DRONE",
        "timestamp": iso8601_utc_now()
    }
    producer.produce(TOPIC_DRONES, key=req.drone_id, value=json.dumps(payload), callback=delivery_report)
    producer.flush(1.0)
    return {"status": "recall_sent", "payload": payload}


@app.post("/manual_move")
async def manual_move(req: ManualMoveRequest):
    payload = {
        "drone_id": req.drone_id,
        "action": "MANUAL_MOVE",
        "position": {"lat": req.lat, "lon": req.lon, "alt": req.alt},
        "timestamp": iso8601_utc_now()
    }
    producer.produce(TOPIC_DRONES, key=req.drone_id, value=json.dumps(payload), callback=delivery_report)
    producer.flush(1.0)
    return {"status": "manual_move_sent", "payload": payload}


@app.post("/resume_auto")
async def resume_auto(req: ResumeAutoRequest):
    payload = {
        "drone_id": req.drone_id,
        "action": "RESUME_AUTO",
        "timestamp": iso8601_utc_now()
    }
    producer.produce(TOPIC_DRONES, key=req.drone_id, value=json.dumps(payload), callback=delivery_report)
    producer.flush(1.0)
    return {"status": "resume_auto_sent", "payload": payload}


@app.get("/health")
async def health():
    return {"status": "up"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
