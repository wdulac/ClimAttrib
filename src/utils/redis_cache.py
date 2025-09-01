import hashlib, json, pickle, os
import redis


redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=1
)


def make_cache_key(event: dict) -> str:
    payload = json.dumps(event, sort_keys=True, default=str).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def set_cache(cache_key: str, value, ttl: int = 60*60*24):
    redis_client.set(cache_key, pickle.dumps(value), ex=ttl)


def cache_exists(*args: list):
    return redis_client.exists(*args) == len(args)


def get_cache(cache_key: str):
    data = redis_client.get(cache_key)
    return pickle.loads(data) if data else None