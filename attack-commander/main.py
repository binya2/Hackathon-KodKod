import os
import json
import argparse
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from confluent_kafka import Producer

# --- Models ---
class EngageRequest(BaseModel):
    action: str
    target_id: str
    drone_id: str

# --- App Initialization ---
app = FastAPI(title="Attack Commander Service")

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_COMMANDS = "commands.attack"

producer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "client.id": "attack-commander"
}
producer = Producer(producer_conf)

def iso8601_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# --- Endpoints ---
@app.post("/engage")
async def engage(req: EngageRequest):
    if req.action != "engage":
        raise HTTPException(status_code=400, detail="Invalid action. Expected 'engage'.")

    # Construct Kafka event
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
            value=json.dumps(payload)
        )
        producer.flush(1) # Ensure delivery for this simple example
        print(f"[CMD] EXECUTE_STRIKE sent for {req.drone_id}")
        return {"status": "command_sent", "payload": payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kafka error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "up"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
