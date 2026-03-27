import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pymongo import DESCENDING
try:
    from .service_manager import run_history_ingestion
    from .db_connection import get_collection, ensure_indexes
except ImportError:
    from service_manager import run_history_ingestion
    from db_connection import get_collection, ensure_indexes

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_indexes()
    ingestion_task = asyncio.create_task(run_history_ingestion())
    yield
    ingestion_task.cancel()
    try:
        await ingestion_task
    except asyncio.CancelledError:
        print('[History] Ingestion task cancelled and stopped.')
app = FastAPI(title='History Service', lifespan=lifespan)

@app.get('/')
async def root():
    return {'status': 'History Service is running'}

@app.get('/drone_history/{drone_id}/{target_id}')
async def get_drone_history(drone_id: str, target_id: str):
    try:
        collection = get_collection('drone_telemetry_history')
        query = {'drone_id': drone_id, 'assigned_target_id': target_id}
        cursor = collection.find(query).sort('timestamp', DESCENDING).limit(40)
        results = list(cursor)
        results.reverse()
        return [doc.get('position') for doc in results if 'position' in doc]
    except Exception as e:
        print(f'[History] Query failed: {e}')
        raise HTTPException(status_code=500, detail='Internal server error while querying history.')
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)