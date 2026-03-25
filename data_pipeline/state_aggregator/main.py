import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from models import WorldState, DroneTelemetry, TargetTelemetry, DroneRole

# %% Global State Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StateAggregator")

# In-memory storage for rapid API access
_global_state = WorldState()
_drones_registry = {}
_targets_registry = {}


# %% Kafka Consumer Task Logic

async def kafka_consumer_task():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    consumer = AIOKafkaConsumer(
        "telemetry.raw", "target.raw",
        bootstrap_servers=bootstrap_servers,
        group_id="state_aggregator_group",
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    await consumer.start()
    try:
        async for msg in consumer:
            if msg.topic == "telemetry.raw":
                try:
                    tel = DroneTelemetry(**msg.value)
                    _drones_registry[tel.drone_id] = tel
                except Exception as e:
                    logger.error(f"Error parsing telemetry: {e}")

            elif msg.topic == "target.raw":
                try:
                    tgt = TargetTelemetry(**msg.value)
                    _targets_registry[tgt.target_id] = tgt
                except Exception as e:
                    logger.error(f"Error parsing target: {e}")

            # Update global state snapshot
            _global_state.timestamp = datetime.utcnow()

            # Recon data sorted: ACTIVE first
            _global_state.recon_data = sorted(
                [d for d in _drones_registry.values() if d.role == DroneRole.RECON],
                key=lambda x: 0 if x.flight_status == "ACTIVE" else 1
            )

            # Attack data sorted: ACTIVE first
            _global_state.attack_data = sorted(
                [d for d in _drones_registry.values() if d.role == DroneRole.ATTACK],
                key=lambda x: 0 if x.flight_status == "ACTIVE" else 1
            )

            _global_state.target_data = list(_targets_registry.values())

    finally:
        await consumer.stop()


# %% Kafka Publisher Task Logic

async def state_publisher_task():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await producer.start()
    try:
        while True:
            payload = _global_state.model_dump_json()
            await producer.send_and_wait("aggregated-state-topic", payload.encode("utf-8"))
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.info("State publisher task cancelled.")
    finally:
        await producer.stop()


# %% FastAPI App & Lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Kafka tasks
    consumer_task = asyncio.create_task(kafka_consumer_task())
    publisher_task = asyncio.create_task(state_publisher_task())
    yield
    # Shutdown
    consumer_task.cancel()
    publisher_task.cancel()
    await asyncio.gather(consumer_task, publisher_task, return_exceptions=True)
    logger.info("Kafka tasks stopped.")


app = FastAPI(title="State Aggregator API", lifespan=lifespan)


@app.get("/api/state", response_model=WorldState)
async def get_state():
    """Returns the latest unified World State."""
    return _global_state


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected.")
    try:
        while True:
            await websocket.send_text(_global_state.model_dump_json())
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# %% Mock Data Generation Cell

# This block can be run in PyCharm/Jupyter to generate a local mock_data.json
# %%
if __name__ == "__main__":
    mock_state = WorldState(
        timestamp=datetime.utcnow(),
        target_data=[{
            "target_id": "TGT_001", "target_type": "vehicle",
            "position": {"lat": 32.1, "lon": 34.8}, "confidence": 0.99
        }],
        recon_data=[{
            "drone_id": "RECON_1", "role": "recon",
            "position": {"lat": 32.11, "lon": 34.81, "alt": 150.0},
            "velocity": 10.0, "heading": 0.0, "battery_percent": 90.0
        }]
    )

    with open("mock_data.json", "w") as f:
        json.dump(mock_state.model_dump(mode='json'), f, indent=4)
    print("Generated mock_data.json")
