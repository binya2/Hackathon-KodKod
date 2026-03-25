import os
import json
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from confluent_kafka import Producer


# --- Models ---
# %% Data Contracts
class EngageRequest(BaseModel):
    action: str
    target_id: str
    drone_id: str


class DeployRequest(BaseModel):
    role: str  # recon or attack


class NewTargetRequest(BaseModel):
    lat: float
    lon: float


# --- App Initialization ---
app = FastAPI(title="Attack Commander Service")

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_COMMANDS = "commands.attack"
TOPIC_DEPLOYMENT = "commands.deployment"
TOPIC_INTEL = "events.intel"


def delivery_report(err, msg):
    if err is not None:
        print(f"[KAFKA-PRODUCER] Failed: {err}")
    else:
        print(f"[KAFKA-PRODUCER] Message sent to {msg.topic()} [{msg.partition()}]")


print(f"[SYSTEM] Attack Commander connecting to Kafka: {KAFKA_BOOTSTRAP}")

producer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "client.id": "attack-commander",
    "allow.auto.create.topics": "true"
}
producer = Producer(producer_conf)


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
        producer.flush(1.0)  # Force delivery
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
        "timestamp": iso8601_utc_now()
    }

    try:
        # Use random UUID as key for random partition routing
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
    """
    Creates a new target and auto-scrambles the first recon drone in one call.
    """
    intel_payload = {
        "action": "SPAWN_TARGET",
        "lat": req.lat,
        "lon": req.lon,
        "timestamp": iso8601_utc_now()
    }
    
    deploy_payload = {
        "action": "DEPLOY_DRONE",
        "role": "recon",
        "timestamp": iso8601_utc_now()
    }

    try:
        # 1. Produce to events.intel
        producer.produce(
            topic=TOPIC_INTEL,
            value=json.dumps(intel_payload),
            callback=delivery_report
        )
        
        # 2. Produce to commands.deployment
        key = str(uuid.uuid4())
        producer.produce(
            topic=TOPIC_DEPLOYMENT,
            key=key,
            value=json.dumps(deploy_payload),
            callback=delivery_report
        )
        
        producer.flush(1.0)
        return {
            "status": "target_spawned_and_recon_deployed",
            "intel_payload": intel_payload,
            "deploy_payload": deploy_payload
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "up"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
