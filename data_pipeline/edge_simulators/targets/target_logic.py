import math
from target_model import TargetState


async def handle_target_event(event_data: dict, topic: str, state: TargetState, producer):
    event_type = event_data.get('action') or event_data.get('event')
    if event_type == 'SPAWN_TARGET':
        await _process_intel(event_data, state, producer)
    elif event_type == 'PAYLOAD_DROPPED':
        await _process_hit(event_data, state, producer)


async def _process_hit(event_data: dict, state: TargetState, producer):
    if not state.is_active:
        return
    event_target_id = event_data.get('target_id')
    if event_target_id and event_target_id != state.target_id:
        return
    drone_lat = event_data.get('lat')
    drone_lon = event_data.get('lon')
    distance = math.sqrt((state.base_lat - drone_lat) ** 2 + (state.base_lon - drone_lon) ** 2)
    if distance < 0.00015:
        state.take_damage(25.0)
        print(f'💥 [DIRECT HIT] {state.target_id} hit! Health: {state.health}')
        await _send_immediate_telemetry(state, producer)
    else:
        print(f'☁️ [MISS] {state.target_id} - Accuracy insufficient. Dist: {distance:.6f}')


async def _send_immediate_telemetry(state: TargetState, producer):
    telemetry = state.create_telemetry(state.base_lat, state.base_lon)
    await producer.send('target.raw', key=state.target_id.encode('utf-8'), value=telemetry.model_dump_json().encode('utf-8'))


async def _process_intel(event_data: dict, state: TargetState, producer):
    action = event_data.get('action')
    if action == 'SPAWN_TARGET':
        target_id = event_data.get('target_id')
        lat = event_data.get('lat')
        lon = event_data.get('lon')
        state.spawn(target_id, lat, lon)
        print(f'🎯 [TARGET SIM] Target {target_id} spawned at {lat}, {lon}')
        await _send_immediate_telemetry(state, producer)
