import math

from target_model import TargetState


def handle_target_event(event_data: dict, topic: str, state: TargetState, producer):
    event_type = event_data.get("action") or event_data.get("event")
    if event_type == "SPAWN_TARGET":
        _process_intel(event_data, state, producer)
    elif event_type == "PAYLOAD_DROPPED":
        _process_hit(event_data, state, producer)


def _process_hit(event_data: dict, state: TargetState, producer):
    if not state.is_active:
        return

    # Check if the hit is intended for this target
    event_target_id = event_data.get("target_id")
    if event_target_id and event_target_id != state.target_id:
        return

    drone_lat = event_data.get("lat")
    drone_lon = event_data.get("lon")

    # Calculate distance to target
    distance = math.sqrt((state.base_lat - drone_lat) ** 2 + (state.base_lon - drone_lon) ** 2)

    # Threshold: 0.00015 is approx 15 meters
    if distance < 0.00015:
        state.take_damage(25.0)
        print(f"💥 [DIRECT HIT] {state.target_id} hit! Health: {state.health}")
        # Send immediate update so the world knows the new health (especially 0%)
        _send_immediate_telemetry(state, producer)
    else:
        print(f"☁️ [MISS] {state.target_id} - Accuracy insufficient. Dist: {distance:.6f}")


def _send_immediate_telemetry(state: TargetState, producer):
    telemetry = state.create_telemetry(state.base_lat, state.base_lon)
    producer.produce(
        "target.raw",
        key=state.target_id,
        value=telemetry.model_dump_json()
    )
    producer.poll(0)


def _process_intel(event_data: dict, state: TargetState, producer):
    """מטפל בפקודות מודיעין כמו יצירת מטרה חדשה"""
    action = event_data.get("action")
    if action == "SPAWN_TARGET":
        target_id = event_data.get("target_id")
        lat = event_data.get("lat")
        lon = event_data.get("lon")

        # יצירת המטרה בסטייט של הסימולטור
        state.spawn(target_id, lat, lon)
        print(f"🎯 [TARGET SIM] Target {target_id} spawned at {lat}, {lon}")

        # שידור מיידי לאגרגטור כדי שהמערכת תראה את המטרה
        _send_immediate_telemetry(state, producer)
