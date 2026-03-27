from datetime import datetime, timezone
from db_connection import get_collection

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