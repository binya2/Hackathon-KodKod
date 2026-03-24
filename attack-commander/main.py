import os
import json
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

def delivery_report(err, msg):
    if err is not None:
        print(f"[KAFKA-PRODUCER] Failed: {err}")
    else:
        print(f"[KAFKA-PRODUCER] Command sent to {msg.topic()} [{msg.partition()}]")

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
        producer.flush(1.0) # Force delivery
        return {"status": "command_sent", "payload": payload}
    except Exception as e:
        print(f"[ERROR] Kafka Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "up"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
