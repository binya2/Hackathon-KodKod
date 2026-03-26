import asyncio
import contextlib

import uvicorn
from fastapi import FastAPI

from data_pipeline.attack_commander.api_endpoints import router
from data_pipeline.attack_commander.kafka_client import (
    init_kafka_producer,
    stop_kafka_producer,
    consume_state_topic
)


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    # הפעלת הפרודיוסר
    await init_kafka_producer()
    # הפעלת משימת הרקע שמאזינה למצב העולם
    consumer_task = asyncio.create_task(consume_state_topic())
    yield
    # כיבוי מסודר
    consumer_task.cancel()
    await stop_kafka_producer()


app = FastAPI(title="Attack Commander Service", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
