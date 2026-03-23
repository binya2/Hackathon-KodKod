import logging

from kafka_client import KafkaClientFactory
from models import TargetPrediction, DroneCommand, CommandType


# %% Recon Brain Service

class ReconBrainService:
    def __init__(self, kafka_factory: KafkaClientFactory):
        self.kafka_factory = kafka_factory
        self.logger = logging.getLogger(self.__class__.__name__)
        self.recon_drone_id = "DRONE_RECON_01"  # In a real system, we'd query available recon drones

    async def run(self):
        # We listen to predictions to decide where to send recon drones
        consumer = self.kafka_factory.create_consumer(['target.predictions'], 'recon_brain_group')
        producer = await self.kafka_factory.get_producer()

        await consumer.start()
        try:
            async for msg in consumer:
                try:
                    prediction = TargetPrediction(**msg.value)

                    # Target center (using first point of polygon as target ref for mock)
                    target_ref = prediction.predicted_polygon[0]

                    # Logic: Command RECON drone to stay 200m above the target center
                    command = DroneCommand(
                        drone_id=self.recon_drone_id,
                        command_type=CommandType.WAYPOINT,
                        params={
                            "lat": target_ref.lat,
                            "lon": target_ref.lon,
                            "alt": 200.0  # Maintain 200m altitude
                        }
                    )

                    await producer.send_and_wait("commands.drones", command.model_dump(mode='json'))
                    self.logger.info(
                        f"Recon Brain: Sent waypoint to {self.recon_drone_id} for target {prediction.target_id}")
                except Exception as e:
                    self.logger.error(f"Recon Brain logic failed: {e}")
        finally:
            await consumer.stop()
