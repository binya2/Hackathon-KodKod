import os
import random
from confluent_kafka import Producer, Consumer

def create_drone_producer(bootstrap_servers: str):
    return Producer({'bootstrap.servers': bootstrap_servers})

def create_drone_consumer(bootstrap_servers: str):
    group_id = f"drone-sim-group-{os.environ.get('HOSTNAME', random.randint(0, 1000))}"
    consumer = Consumer({'bootstrap.servers': bootstrap_servers, 'group.id': group_id, 'auto.offset.reset': 'earliest', 'enable.auto.commit': True})
    consumer.subscribe(['commands.drones', 'commands.attack'])
    return consumer