import json
import os
import redis.asyncio as redis

redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'), decode_responses=True)


def parse_redis_hash(redis_hash_data: dict) -> list:
    parsed_data = []
    for v in redis_hash_data.values():
        try:
            parsed_data.append(json.loads(v))
        except Exception:
            pass
    return parsed_data
