import os

from pymongo import MongoClient
from pymongo.errors import PyMongoError


def get_collection():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "history_archive_db")
    collection_name = os.getenv("MONGO_COLLECTION_NAME", "state_history")

    if not mongo_uri:
        raise ValueError("MONGO_URI is not set.")

    try:
        print("[MongoDB] Connecting to MongoDB...")
        client = MongoClient(mongo_uri)
        collection = client[db_name][collection_name]
        print(f"[MongoDB] Connected. Using {db_name}.{collection_name}")
        return collection
    except PyMongoError as exc:
        print(f"[MongoDB] Connection failed: {exc}")
        raise
