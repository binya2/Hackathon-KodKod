import os
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
        collection.create_index([('drone_id', ASCENDING), ('assigned_target_id', ASCENDING), ('timestamp', DESCENDING)], background=True)
        print('[MongoDB] Indexes ensured.')
    except Exception as e:
        print(f'[MongoDB] Error creating indexes: {e}')