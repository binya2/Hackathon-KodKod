import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pymongo import DESCENDING

# Use relative imports when running as a package or direct imports when running as a script
try:
    from .service_manager import run_history_ingestion
    from .db_connection import get_collection, ensure_indexes
except ImportError:
    from service_manager import run_history_ingestion
    from db_connection import get_collection, ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI app."""
    # Initialization
    ensure_indexes()
    
    # Start the ingestion task in the background
    ingestion_task = asyncio.create_task(run_history_ingestion())
    
    yield
    
    # Shutdown
    ingestion_task.cancel()
    try:
        await ingestion_task
    except asyncio.CancelledError:
        print("[History] Ingestion task cancelled and stopped.")


app = FastAPI(title="History Service", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "History Service is running"}


@app.get("/drone_history/{drone_id}/{target_id}")
async def get_drone_history(drone_id: str, target_id: str):
    """
    Returns the last 40 position records for a specific drone and its assigned target.
    Sorted from oldest to newest.
    """
    try:
        collection = get_collection("drone_telemetry_history")
        
        # Query matching drone_id and target_id
        query = {
            "drone_id": drone_id,
            "assigned_target_id": target_id
        }
        
        # Sort by timestamp DESC to get the MOST RECENT 40
        cursor = collection.find(query).sort("timestamp", DESCENDING).limit(40)
        
        # Extract positions and reverse the order (oldest -> newest)
        results = list(cursor)
        results.reverse()
        
        # Return only the list of positions
        return [doc.get("position") for doc in results if "position" in doc]
        
    except Exception as e:
        print(f"[History] Query failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while querying history.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
