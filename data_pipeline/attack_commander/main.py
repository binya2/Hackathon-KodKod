import json
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from models import (
    EngageRequest, DeployRequest, NewTargetRequest,
    RecallRequest, ManualMoveRequest, ResumeAutoRequest
)
from kafka_client import producer, delivery_report

# --- App Initialization ---
app = FastAPI(title="Attack Commander Service")

# --- Constants ---
TOPIC_COMMANDS = "commands.attack"
TOPIC_DEPLOYMENT = "commands.deployment"
TOPIC_INTEL = "events.intel"
TOPIC_DRONES = "commands.drones"


def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# --- Endpoints ---
# %% API Endpoints

@app.post("/engage")
async def engage(req: EngageRequest):
    print(f"[API] Engage: {req.drone_id} vs {req.target_id}")

    if req.action != "engage":
        raise HTTPException(status_code=400, detail="Invalid action.")

    payload = {
        "drone_id": req.drone_id,
        "action": "EXECUTE_STRIKE",
        "target_id": req.target_id,
        "timestamp": iso8601_utc_now()
    }

    try:
        producer.produce(
            topic=TOPIC_COMMANDS,
            key=req.drone_id,
            value=json.dumps(payload),
            callback=delivery_report
        )
        producer.flush(1.0)
        return {"status": "command_sent", "payload": payload}
    except Exception as e:
        print(f"[ERROR] Kafka Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/deploy_drone")
async def deploy_drone(req: DeployRequest):
    if req.role not in ["recon", "attack"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'recon' or 'attack'.")

    payload = {
        "action": "DEPLOY_DRONE",
        "role": req.role,
        "target_id": req.target_id,
        "timestamp": iso8601_utc_now()
    }

    try:
        key = str(uuid.uuid4())
        producer.produce(
            topic=TOPIC_DEPLOYMENT,
            key=key,
            value=json.dumps(payload),
            callback=delivery_report
        )
        producer.flush(1.0)
        return {"status": "deployment_request_sent", "payload": payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/new_target")
async def new_target(req: NewTargetRequest):
    target_id = "TGT-1"
    intel_payload = {
        "action": "SPAWN_TARGET",
        "lat": req.lat,
        "lon": req.lon,
        "timestamp": iso8601_utc_now()
    }

    try:
        producer.produce(
            topic=TOPIC_INTEL,
            value=json.dumps(intel_payload),
            callback=delivery_report
        )

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
        return {
            "status": "target_spawned_and_swarm_deployed",
            "intel_payload": intel_payload,
            "deployment_count": len(deployments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
