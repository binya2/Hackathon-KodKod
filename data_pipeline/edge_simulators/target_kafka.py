import os
import random
from confluent_kafka import Producer, Consumer


def create_target_producer(bootstrap_servers: str):
    return Producer({"bootstrap.servers": bootstrap_servers})


def create_target_consumer(bootstrap_servers: str):
    # Use earliest to ensure we don't miss the first SPAWN_TARGET event
    # even if the simulator starts slightly after the command is sent.
    group_id = f"target-sim-group-{os.environ.get('HOSTNAME', random.randint(0, 1000))}"
    
    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest", 
        "enable.auto.commit": True
    })
    consumer.subscribe(["events.mission"])
    return consumer
