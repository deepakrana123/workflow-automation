import os
from redis import Redis

redis_client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"), port=6379, decode_responses=True
)
