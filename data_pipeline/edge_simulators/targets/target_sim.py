import argparse
import json
import os
import asyncio
import random
from target_model import TargetState
from target_logic import handle_target_event
from data_pipeline.shared.kafka_utils import get_kafka_producer, get_kafka_consumer


async def main():
    parser = argparse.ArgumentParser(description='Target Simulator')
    parser.add_argument('--kafka-bootstrap', type=str,
                        default=os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))
    args = parser.parse_args()
    producer = await get_kafka_producer(args.kafka_bootstrap)
    consumer = await get_kafka_consumer(['events.mission'], 
                                        f"target-sim-group-{os.environ.get('HOSTNAME', 'default')}",
                                        args.kafka_bootstrap)
    state = TargetState()
    await producer.start()
    await consumer.start()
    print(f'[TARGET] Simulator running. Connecting to {args.kafka_bootstrap}')
    try:
        while True:
            await _poll_events(consumer, state, producer)
            await _emit_telemetry(state, producer)
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        print('[SYSTEM] Stopped manually.')
    finally:
        await producer.stop()
        await consumer.stop()


async def _poll_events(consumer, state, producer):
    msgs = await consumer.getmany(timeout_ms=10)
    for topic, tp_msgs in msgs.items():
        for msg in tp_msgs:
            try:
                event_data = json.loads(msg.value.decode('utf-8'))
                await handle_target_event(event_data, topic.topic, state, producer)
            except Exception as e:
                print(f'[Error] Failed to process event: {e}')


async def _emit_telemetry(state, producer):
    if not state.is_active:
        if state._death_broadcasted or state.target_id == 'TGT-INIT':
            return
        state._death_broadcasted = True
    jitter_lat = state.base_lat + random.uniform(-2e-05, 2e-05)
    jitter_lon = state.base_lon + random.uniform(-2e-05, 2e-05)
    telemetry = state.create_telemetry(jitter_lat, jitter_lon)
    await producer.send('target.raw', key=state.target_id.encode('utf-8'), value=telemetry.model_dump_json().encode('utf-8'))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
