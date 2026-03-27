import asyncio
import logging

from aiokafka import AIOKafkaProducer

from data_pipeline.attack_brain.navigation_calculator import calculate_waypoint, calculate_distance_m
from data_pipeline.attack_brain.state_manager import get_active_attack_drones, get_target, get_active_targets, \
    get_drones_on_target
from data_pipeline.attack_brain.target_evaluator import evaluate_target_needs, find_new_target, recall_drone, \
    request_replacement
from data_pipeline.shared.models import DroneCommand

logger = logging.getLogger(__name__)


async def assignment_loop(producer: AIOKafkaProducer):
    while True:
        all_drones = await get_active_attack_drones()
        active_targets = await get_active_targets()
        for target in active_targets:
            await evaluate_target_needs(target, all_drones, producer)
        for drone in all_drones:
            if drone.flight_status != 'MANUAL' and drone.assigned_target_id:
                await _process_drone_assignment(drone, producer, all_drones, active_targets)
        await asyncio.sleep(1.0)


async def _process_drone_assignment(drone, producer, all_drones, active_targets):
    target = await get_target(drone.assigned_target_id)
    if not target or target.health <= 0:
        target = find_new_target(active_targets, all_drones)
        if not target:
            return await recall_drone(drone.drone_id, producer)
    if drone.flight_status == 'ATTACKING':
        return
    if drone.role == 'attack' and drone.weapons_count == 0:
        await request_replacement(target, producer)
        return await recall_drone(drone.drone_id, producer)
    await _send_drone_waypoint(drone, target, producer)


async def _send_drone_waypoint(drone, target, producer):
    drones_on_target = await get_drones_on_target(drone.assigned_target_id)
    index = next((i for i, d in enumerate(drones_on_target) if d.drone_id == drone.drone_id), 0)
    waypoint = calculate_waypoint(target.position, index)
    dist_m = calculate_distance_m(drone.position, target.position)
    cmd = DroneCommand(drone_id=drone.drone_id, position=waypoint,
                       flight_status='ACTIVE' if dist_m <= 20.0 else 'EN_ROUTE')
    await producer.send_and_wait('commands.drones', cmd.model_dump_json().encode('utf-8'))
