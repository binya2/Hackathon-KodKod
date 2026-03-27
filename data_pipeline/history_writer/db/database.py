import os
from datetime import datetime, timezone
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import PyMongoError


def get_db():
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGO_DB_NAME', 'history_archive_db')
    if not mongo_uri:
        raise ValueError('MONGO_URI is not set.')
    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        return db
    except PyMongoError as exc:
        print(f'[MongoDB] Connection failed: {exc}')
        raise


def get_collection(collection_name='drone_telemetry_history'):
    db = get_db()
    return db[collection_name]


def ensure_indexes():
    try:
        collection = get_collection('drone_telemetry_history')
        print('[MongoDB] Ensuring indexes for drone_telemetry_history...')
        collection.create_index([('drone_id', ASCENDING), ('assigned_target_id', ASCENDING), ('timestamp', DESCENDING)],
                                background=True)
        print('[MongoDB] Indexes ensured.')
    except Exception as e:
        print(f'[MongoDB] Error creating indexes: {e}')


def insert_state_batch(state_list: list):
    try:
        if not state_list:
            return None
        now_iso = datetime.now(timezone.utc).isoformat()
        for doc in state_list:
            if 'archived_at' not in doc:
                doc['archived_at'] = now_iso
        collection = get_collection()
        result = collection.insert_many(state_list)
        print(f'[DB CRUD] Inserted batch of {len(result.inserted_ids)} documents.')
        return result.inserted_ids
    except Exception as exc:
        print(f'[DB CRUD] Batch insert failed: {exc}')
        return None


def archive_state_batch(states: list):
    if not states:
        return
    timestamped_states = _add_archive_timestamps(states)
    try:
        collection = get_collection()
        result = collection.insert_many(timestamped_states)
        print(f'[DB] Archived {len(result.inserted_ids)} states.')
    except Exception as e:
        print(f'[DB] Archive failed: {e}')


def _add_archive_timestamps(states: list):
    now_iso = datetime.now(timezone.utc).isoformat()
    for state in states:
        if 'archived_at' not in state:
            state['archived_at'] = now_iso
    return states
