import json
import logging
from datetime import datetime, timezone
from data_pipeline.shared.models import WorldState, DroneTelemetry, TargetTelemetry
from data_pipeline.shared.redis_utils import redis_client

logger = logging.getLogger(__name__)


async def update_drone_telemetry(telemetry: DroneTelemetry):
    current_raw = await redis_client.hget('drones', telemetry.drone_id)
    if current_raw:
        current_data = json.loads(current_raw)
        new_data = telemetry.model_dump(mode='json')
        is_ghost_sleep = current_data.get('flight_status') in ['EN_ROUTE', 'ACTIVE', 'ATTACKING'] and new_data.get(
            'flight_status') == 'SLEEP'
        if is_ghost_sleep:
            current_data['position'] = new_data['position']
            current_data['velocity'] = new_data['velocity']
            current_data['heading'] = new_data['heading']
            current_data['battery_percent'] = new_data['battery_percent']
            current_data['timestamp'] = new_data['timestamp']
            await redis_client.hset('drones', telemetry.drone_id, json.dumps(current_data))
        else:
            await redis_client.hset('drones', telemetry.drone_id, json.dumps(new_data))
    else:
        await redis_client.hset('drones', telemetry.drone_id, telemetry.model_dump_json())


async def update_target_telemetry(telemetry: TargetTelemetry):
    await redis_client.hset('targets', telemetry.target_id, telemetry.model_dump_json())


async def garbage_collect_stale_drones():
    now = datetime.now(timezone.utc)
    drones_raw = await redis_client.hgetall('drones')
    for drone_id, drone_json in drones_raw.items():
        try:
            drone = DroneTelemetry.model_validate_json(drone_json)
            if (now - drone.timestamp).total_seconds() > 15.0:
                logger.warning(f'Removing stale drone %s from state (no telemetry for >15s)', drone_id)
                await redis_client.hdel('drones', drone_id)
        except Exception as e:
            logger.error(f'Error parsing drone {drone_id}: {e}')
            await redis_client.hdel('drones', drone_id)


async def garbage_collect_dead_targets():
    now = datetime.now(timezone.utc)
    targets_raw = await redis_client.hgetall('targets')
    for target_id, target_json in targets_raw.items():
        try:
            target = TargetTelemetry.model_validate_json(target_json)
            if target.health <= 0 and (now - target.timestamp).total_seconds() > 30.0:
                logger.info(f'Removing dead target %s from state (dead for >30s)', target_id)
                await redis_client.hdel('targets', target_id)
        except Exception as e:
            logger.error(f'Error parsing target {target_id}: {e}')


def _parse_drones_from_redis(drones_raw: dict) -> list:
    drones = []
    for v in drones_raw.values():
        try:
            drones.append(DroneTelemetry.model_validate_json(v))
        except Exception as e:
            logger.error(f'Error parsing drone telemetry: {e}')
    return drones


def _parse_targets_from_redis(targets_raw: dict) -> list:
    targets = []
    for v in targets_raw.values():
        try:
            targets.append(TargetTelemetry.model_validate_json(v))
        except Exception as e:
            logger.error(f'Error parsing target telemetry: {e}')
    return targets


async def get_world_state() -> WorldState:
    await garbage_collect_stale_drones()
    await garbage_collect_dead_targets()
    drones_raw = await redis_client.hgetall('drones')
    targets_raw = await redis_client.hgetall('targets')
    drones = _parse_drones_from_redis(drones_raw)
    targets = _parse_targets_from_redis(targets_raw)
    world_state = WorldState()
    world_state.timestamp = datetime.now(timezone.utc)
    world_state.recon_data = sorted([d for d in drones if d.role.lower() == 'recon'],
                                    key=lambda x: 0 if x.flight_status == 'ACTIVE' else 1)
    world_state.attack_data = sorted([d for d in drones if d.role.lower() == 'attack'],
                                     key=lambda x: 0 if x.flight_status == 'ACTIVE' else 1)
    world_state.target_data = targets
    return world_state
