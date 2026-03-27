import asyncio
import logging
from datetime import datetime
try:
    from .kafka_service import create_history_consumer, poll_and_decode_messages
    from .db_connection import get_collection
except ImportError:
    from kafka_service import create_history_consumer, poll_and_decode_messages
    from db_connection import get_collection
logger = logging.getLogger(__name__)

async def run_history_ingestion():
    consumer = create_history_consumer()
    collection = get_collection('drone_telemetry_history')
    print('[History] Ingestion task started.')
    try:
        while True:
            message = poll_and_decode_messages(consumer, timeout=0.1)
            if message:
                await process_world_state(message, collection)
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        print('[History] Ingestion task stopping...')
    finally:
        consumer.close()

async def process_world_state(state: dict, collection):
    drone_docs = []
    for d in state.get('recon_data', []):
        doc = {'drone_id': d.get('drone_id'), 'assigned_target_id': d.get('assigned_target_id'), 'position': d.get('position'), 'timestamp': d.get('timestamp')}
        drone_docs.append(doc)
    for d in state.get('attack_data', []):
        doc = {'drone_id': d.get('drone_id'), 'assigned_target_id': d.get('assigned_target_id'), 'position': d.get('position'), 'timestamp': d.get('timestamp')}
        drone_docs.append(doc)
    if drone_docs:
        try:
            collection.insert_many(drone_docs)
        except Exception as e:
            logger.error(f'[History] Failed to insert drone telemetry: {e}')