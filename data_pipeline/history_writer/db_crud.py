from datetime import datetime, timezone

from db_connection import get_collection


# %% Database Operations
def insert_state_batch(state_list: list):
    try:
        if not state_list:
            return None

        # Add timestamp to each doc
        now_iso = datetime.now(timezone.utc).isoformat()
        for doc in state_list:
            if "archived_at" not in doc:
                doc["archived_at"] = now_iso

        collection = get_collection()
        result = collection.insert_many(state_list)
        print(f"[DB CRUD] Inserted batch of {len(result.inserted_ids)} documents.")
        return result.inserted_ids
    except Exception as exc:
        print(f"[DB CRUD] Batch insert failed: {exc}")
        return None
