from datetime import datetime, timezone

from db_connection import get_collection


def insert_state_document(state_data: dict):
    try:
        if not isinstance(state_data, dict):
            print("[DB CRUD] Skipping insert: message is not a dict.")
            return None

        if "archived_at" not in state_data:
            state_data["archived_at"] = datetime.now(timezone.utc).isoformat()

        collection = get_collection()
        result = collection.insert_one(state_data)
        print(f"[DB CRUD] Inserted document with id: {result.inserted_id}")
        return result.inserted_id
    except Exception as exc:
        print(f"[DB CRUD] Insert failed: {exc}")
        return None
