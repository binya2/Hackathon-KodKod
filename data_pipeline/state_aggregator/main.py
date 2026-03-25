import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from data_pipeline.shared_models import WorldState, DroneTelemetry, TargetTelemetry, DroneRole, GeoPoint, TargetType
from data_pipeline.state_aggregator.kafka_service import kafka_consumer_task, state_publisher_task
from data_pipeline.state_aggregator.state_manager import get_world_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StateAggregator")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    consumer_task = asyncio.create_task(kafka_consumer_task())
    publisher_task = asyncio.create_task(state_publisher_task())
    yield
    consumer_task.cancel()
    publisher_task.cancel()
    await asyncio.gather(consumer_task, publisher_task, return_exceptions=True)
    logger.info("Kafka tasks stopped.")


app = FastAPI(title="State Aggregator API", lifespan=lifespan)


@app.get("/api/state", response_model=WorldState)
async def get_state():
    return get_world_state()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected.")
    try:
        while True:
            current_state = get_world_state()
            await websocket.send_text(current_state.model_dump_json())
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception:
        logger.exception("WebSocket error")


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
