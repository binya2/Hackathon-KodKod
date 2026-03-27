import contextlib
import uvicorn
from fastapi import FastAPI
from data_pipeline.attack_commander.routers.api_endpoints import router
from data_pipeline.attack_commander.services.kafka_client import init_kafka_producer, stop_kafka_producer


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_kafka_producer()
    yield
    await stop_kafka_producer()


app = FastAPI(title='Attack Commander Service', lifespan=lifespan)
app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
