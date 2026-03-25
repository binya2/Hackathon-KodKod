import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from data_pipeline.shared_models import WorldState, DroneTelemetry, TargetTelemetry, DroneRole, GeoPoint, TargetType

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

    # We remove value_deserializer because msg.value will be bytes. We handle it explicitly.
    consumer = AIOKafkaConsumer(
        "telemetry.raw", "target.raw",
        bootstrap_servers=bootstrap_servers,
        group_id="state_aggregator_group"
    )

    await consumer.start()
    try:
        async for msg in consumer:
            if not msg.value:
                continue

            try:
                # Standardized JSON decoding
                raw_data = json.loads(msg.value.decode("utf-8"))
            except Exception:
                logger.exception("Error decoding JSON message")
                continue

            if msg.topic == "telemetry.raw":
                try:
                    tel = DroneTelemetry.model_validate(raw_data)
                    _drones_registry[tel.drone_id] = tel
                except Exception:
                    logger.exception("Error parsing telemetry")

            elif msg.topic == "target.raw":
                try:
                    tgt = TargetTelemetry.model_validate(raw_data)
                    _targets_registry[tgt.target_id] = tgt
                except Exception:
                    logger.exception("Error parsing target")

            # --- Garbage Collection (Zombie Drones) ---
            now = datetime.now(timezone.utc)
            stale_drones = []
            for d_id, drone in _drones_registry.items():
                # Remove drones that haven't sent telemetry in the last 5 seconds
                if (now - drone.timestamp).total_seconds() > 5.0:
                    stale_drones.append(d_id)

            for d_id in stale_drones:
                logger.warning(f"Removing stale drone {d_id} from state (no telemetry for >5s)")
                del _drones_registry[d_id]
            # ------------------------------------------

            # Update global state snapshot
            _global_state.timestamp = now

            # Recon data sorted: ACTIVE first
            _global_state.recon_data = sorted(
                [d for d in _drones_registry.values() if d.role == DroneRole.RECON.value],
                key=lambda x: 0 if x.flight_status == "ACTIVE" else 1
            )

            # Attack data sorted: ACTIVE first
            _global_state.attack_data = sorted(
                [d for d in _drones_registry.values() if d.role == DroneRole.ATTACK.value],
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
async def lifespan(_app: FastAPI):
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
    except Exception:
        logger.exception("WebSocket error")


# %% Mock Data Generation Cell

# This block can be run in PyCharm/Jupyter to generate a local mock_data.json
# %%
if __name__ == "__main__":
    mock_state = WorldState(
        timestamp=datetime.now(timezone.utc),

        target_data=[
            TargetTelemetry(
                target_id="TGT_001",
                target_type=TargetType.VEHICLE.value,
                position=GeoPoint(lat=32.1, lon=34.8),
                confidence=0.99
            )
        ],

        recon_data=[
            DroneTelemetry(
                drone_id="RECON_1",
                role=DroneRole.RECON.value,
                position=GeoPoint(lat=32.11, lon=34.81, alt=150.0),
                velocity=10.0,
                heading=0.0,
                battery_percent=90.0,
                flight_status="ACTIVE"
            )
        ]
    )

    with open("mock_data.json", "w") as f:
        json.dump(mock_state.model_dump(mode='json'), f, indent=4)
    print("Generated mock_data.json")
