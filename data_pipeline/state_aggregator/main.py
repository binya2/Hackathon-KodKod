import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI

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
            _global_state.recon_data = [d for d in _drones_registry.values() if d.role == DroneRole.RECON]
            _global_state.attack_data = [d for d in _drones_registry.values() if d.role == DroneRole.ATTACK]
            _global_state.target_data = list(_targets_registry.values())

    finally:
        await consumer.stop()


# %% FastAPI App & Lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Kafka consumer background task
    task = asyncio.create_task(kafka_consumer_task())
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Kafka consumer task stopped.")


app = FastAPI(title="State Aggregator API", lifespan=lifespan)


@app.get("/api/state", response_model=WorldState)
async def get_state():
    """Returns the latest unified World State."""
    return _global_state


# %% Mock Data Generation Cell

# This block can be run in PyCharm/Jupyter to generate a local mock_data.json
# %%
if __name__ == "__main__":
    import json
    from datetime import datetime

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
