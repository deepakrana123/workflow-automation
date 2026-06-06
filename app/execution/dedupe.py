from app.core.redis_client import redis_client


def acquire_distributed_lock(event_id: str, workflow_id: int, ttl_seconds: int = 3600) -> bool:
    """
    Acquire a Redis NX lock for a specific (event_id, workflow_id) pair.
    Returns True if lock was acquired (safe to proceed), False if already locked (duplicate).
    """
    key = f"exec:{event_id}:{workflow_id}"
    return bool(redis_client.set(key, 1, nx=True, ex=ttl_seconds))


def is_duplicate_execution(event_id: str, workflow_id: int) -> bool:
    """
    Check if a distributed lock already exists for this (event_id, workflow_id).
    Does NOT acquire the lock — use acquire_distributed_lock for that.
    """
    key = f"exec:{event_id}:{workflow_id}"
    return redis_client.exists(key) == 1
