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