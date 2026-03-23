import logging
from models import TargetTelemetry, TargetPrediction, GeoPoint
from kafka_client import KafkaClientFactory


# %% Predictor Service

class PredictorService:
    def __init__(self, kafka_factory: KafkaClientFactory):
        self.kafka_factory = kafka_factory
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        consumer = self.kafka_factory.create_consumer(['target.raw'], 'predictor_group')
        producer = await self.kafka_factory.get_producer()

        await consumer.start()
        try:
            async for msg in consumer:
                try:
                    target = TargetTelemetry(**msg.value)

                    # Mock Logic: Create a "Predicted Polygon" (square) by offsetting 0.001 deg
                    offset = 0.001
                    polygon = [
                        GeoPoint(lat=target.position.lat + offset, lon=target.position.lon + offset),
                        GeoPoint(lat=target.position.lat + offset, lon=target.position.lon - offset),
                        GeoPoint(lat=target.position.lat - offset, lon=target.position.lon - offset),
                        GeoPoint(lat=target.position.lat - offset, lon=target.position.lon + offset),
                    ]

                    prediction = TargetPrediction(
                        target_id=target.target_id,
                        predicted_polygon=polygon,
                        time_horizon_sec=30.0
                    )

                    await producer.send_and_wait("target.predictions", prediction.model_dump(mode='json'))
                    self.logger.debug(f"Prediction generated for target {target.target_id}")
                except Exception as e:
                    self.logger.error(f"Prediction failed: {e}")
        finally:
            await consumer.stop()
