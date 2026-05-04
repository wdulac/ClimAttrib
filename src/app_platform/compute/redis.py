"""
Redis cache layer — DB 1.

Wraps a Redis client connected to DB 1 (separate from the Celery broker on DB 0) and
provides helpers for storing and retrieving attribution results.

Cache entries are pickled Python dicts with a ``'status'`` key (``'ok'`` or
``'timeout'``) and, for successful results, a ``'result'`` key containing an
``xarray.Dataset``.

Public API:

- ``make_cache_key(event)`` — SHA-256 of the JSON-sorted event dict; same event always
  produces the same key.
- ``set_cache(key, value, ttl)`` — pickle and store with expiry (default 48 h).
- ``get_cache(key)`` — retrieve, unpickle, and reset TTL; returns ``None`` if missing.
- ``cache_exists(*keys)`` — returns True only if all supplied keys are present.
- ``delete_cache(key)`` — remove a single entry.
- ``redis_client`` — the raw ``redis.Redis`` instance, used directly by admin routes.
"""

import hashlib, json, pickle, os
import redis
import xarray

REDIS_TTL=60*60*48 # 48 hours caching
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6380'))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=1
)


def make_cache_key(event: dict) -> str:
    """
    Create redis key based on an event dict
    """

    payload = json.dumps(event, sort_keys=True, default=str).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def set_cache(cache_key: str, value: dict, ttl: int = REDIS_TTL):
    """
    Store attribution dataset to redis with expiration duration
    """

    redis_client.set(cache_key, pickle.dumps(value), ex=ttl)


def delete_cache(cache_key: str):
    """
    Delete a cached entry
    """

    redis_client.delete(cache_key)


def cache_exists(*args: list) -> bool:
    """
    Returns true if all keys received as parameters exist in the Redis database
    """

    return redis_client.exists(*args) == len(args)


def get_cache(cache_key: str, reset_ttl=REDIS_TTL) -> xarray.Dataset:
    """
    Retrieves stored value associated with a given key and extends the expiration duration.

    Returns None if the key doesn't exist in Redis
    """
    
    data = redis_client.get(cache_key)
    if data and reset_ttl:
        redis_client.expire(cache_key, reset_ttl)
    return pickle.loads(data) if data else None