import argparse
import json
import os
import time
from drone_manager import DroneManager
from drone_kafka import create_drone_producer, create_drone_consumer
BASE_LAT = 31.8
BASE_LON = 35.1

def main():
    parser = argparse.ArgumentParser(description='Drone Swarm Simulator')
    parser.add_argument('--num-drones', type=int, default=20)
    parser.add_argument('--kafka-bootstrap', type=str, default=os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))
    args = parser.parse_args()
    producer = create_drone_producer(args.kafka_bootstrap)
    consumer = create_drone_consumer(args.kafka_bootstrap)
    manager = DroneManager(args.num_drones, BASE_LAT, BASE_LON)
    for _ in range(5):
        for drone in manager.drones:
            telemetry = drone.to_telemetry()
            producer.produce('telemetry.raw', key=drone.drone_id, value=telemetry.model_dump_json())
        producer.flush()
        time.sleep(0.5)
    print(f'[DroneSim] Running {args.num_drones} drones. Connected to {args.kafka_bootstrap}')
    try:
        while True:
            _poll_commands(consumer, manager, producer)
            _update_and_emit_telemetry(manager, producer)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('[System] Stopping Drone Simulator.')
    finally:
        producer.flush()
        consumer.close()

def _poll_commands(consumer, manager, producer):
    while True:
        msg = consumer.poll(0.0)
        if msg is None or msg.error():
            break
        try:
            cmd_data = json.loads(msg.value().decode('utf-8'))
            manager.handle_command(cmd_data, msg.topic(), producer)
        except Exception as e:
            print(f'[Error] Command processing failed: {e}')

def _update_and_emit_telemetry(manager, producer):
    manager.update_all(0.1, producer)
    for drone in manager.drones:
        telemetry = drone.to_telemetry()
        producer.produce('telemetry.raw', key=drone.drone_id, value=telemetry.model_dump_json())
    producer.poll(0)
if __name__ == '__main__':
    main()