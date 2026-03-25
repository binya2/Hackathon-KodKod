import contextlib

import uvicorn
from fastapi import FastAPI

from data_pipeline.attack_commander.api_endpoints import router
from data_pipeline.attack_commander.kafka_client import producer


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    print("Flushing Kafka producer on shutdown...")
    producer.flush()


app = FastAPI(title="Attack Commander Service", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
