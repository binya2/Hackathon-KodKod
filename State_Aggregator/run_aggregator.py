import asyncio
import logging
import sys
from kafka_client import KafkaClientFactory
from aggregator_service import StateAggregatorService

# %% Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("AggregatorLauncher")

# %% Main Execution Logic

async def main():
    # 1. Initialize Kafka Factory (assumes Kafka is running on localhost:9092)
    kafka_factory = KafkaClientFactory(bootstrap_servers="localhost:9092")
    
    # 2. Initialize the Aggregator Service
    aggregator = StateAggregatorService(kafka_factory)
    
    logger.info("Starting State Aggregator Service...")
    
    try:
        # 3. Start the service (Consumption + Emission loops)
        await aggregator.start()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received.")
    except Exception as e:
        logger.error(f"Service crashed: {e}")
    finally:
        # 4. Cleanup
        aggregator.stop()
        await kafka_factory.close_producer()
        logger.info("Service stopped gracefully.")

if __name__ == "__main__":
    # Run the async main loop
    asyncio.run(main())
