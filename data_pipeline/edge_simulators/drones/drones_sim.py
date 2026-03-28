import argparse
import json
import os
import asyncio
from drone_manager import DroneManager
from data_pipeline.shared.kafka_utils import get_kafka_producer, get_kafka_consumer

BASE_LAT = 31.8
BASE_LON = 35.1


async def main():
    parser = argparse.ArgumentParser(description='Drone Swarm Simulator')
    parser.add_argument('--num-drones', type=int, default=20)
    parser.add_argument('--kafka-bootstrap', type=str,
                        default=os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))
    args = parser.parse_args()
    producer = await get_kafka_producer(args.kafka_bootstrap)
    consumer = await get_kafka_consumer(['commands.drones', 'commands.attack'], 
                                        f"drone-sim-group-{os.environ.get('HOSTNAME', 'default')}",
                                        args.kafka_bootstrap)
    manager = DroneManager(args.num_drones, BASE_LAT, BASE_LON)
    await producer.start()
    await consumer.start()
    print(f'[DroneSim] Running {args.num_drones} drones. Connected to {args.kafka_bootstrap}')
    try:
        while True:
            await _poll_commands(consumer, manager, producer)
            await _update_and_emit_telemetry(manager, producer)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print('[System] Stopping Drone Simulator.')
    finally:
        await producer.stop()
        await consumer.stop()


async def _poll_commands(consumer, manager, producer):
    msgs = await consumer.getmany(timeout_ms=10)
    for topic, tp_msgs in msgs.items():
        for msg in tp_msgs:
            try:
                cmd_data = json.loads(msg.value.decode('utf-8'))
                await manager.handle_command(cmd_data, topic.topic, producer)
            except Exception as e:
                print(f'[Error] Command processing failed: {e}')


async def _update_and_emit_telemetry(manager, producer):
    await manager.update_all(0.1, producer)
    for drone in manager.drones:
        telemetry = drone.to_telemetry()
        await producer.send('telemetry.raw', key=drone.drone_id.encode('utf-8'), value=telemetry.model_dump_json().encode('utf-8'))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
