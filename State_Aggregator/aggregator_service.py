import asyncio
import logging
from datetime import datetime
from typing import Dict
from models import DroneTelemetry, TargetTelemetry, WorldState, DroneRole
from kafka_client import KafkaClientFactory


# %% State Aggregator Service

class StateAggregatorService:
    def __init__(self, kafka_factory: KafkaClientFactory):
        self.kafka_factory = kafka_factory
        self.logger = logging.getLogger(self.__class__.__name__)

        # In-memory stores (latest state only)
        self.drone_registry: Dict[str, DroneTelemetry] = {}
        self.target_registry: Dict[str, TargetTelemetry] = {}

        self.is_running = False

    async def consume_telemetry(self):
        """Task for consuming drone telemetry"""
        consumer = self.kafka_factory.create_consumer(['telemetry.raw'], 'aggregator_group')
        await consumer.start()
        try:
            async for msg in consumer:
                try:
                    telemetry = DroneTelemetry(**msg.value)
                    self.drone_registry[telemetry.drone_id] = telemetry
                except Exception as e:
                    self.logger.error(f"Failed to parse telemetry: {e}")
        finally:
            await consumer.stop()

    async def consume_targets(self):
        """Task for consuming target detections"""
        consumer = self.kafka_factory.create_consumer(['target.raw'], 'aggregator_group')
        await consumer.start()
        try:
            async for msg in consumer:
                try:
                    target = TargetTelemetry(**msg.value)
                    self.target_registry[target.target_id] = target
                except Exception as e:
                    self.logger.error(f"Failed to parse target: {e}")
        finally:
            await consumer.stop()

    async def emission_loop(self, interval_ms: int = 500):
        """Periodic task to output unified world state"""
        producer = await self.kafka_factory.get_producer()
        while self.is_running:
            # Build current snapshot
            recon_drones = [d for d in self.drone_registry.values() if d.role == DroneRole.RECON]
            attack_drones = [d for d in self.drone_registry.values() if d.role == DroneRole.ATTACK]

            world_state = WorldState(
                timestamp=datetime.now(),
                target_data=list(self.target_registry.values()),
                recon_data=recon_drones,
                attack_data=attack_drones
            )

            # Send to world.state topic
            await producer.send_and_wait("world.state", world_state.model_dump(mode='json'))
            self.logger.debug(f"Emitted world state with {len(world_state.target_data)} targets")

            await asyncio.sleep(interval_ms / 1000.0)

    async def start(self):
        self.is_running = True
        # Run consumers and emission loop concurrently
        await asyncio.gather(
            self.consume_telemetry(),
            self.consume_targets(),
            self.emission_loop()
        )

    def stop(self):
        self.is_running = False
