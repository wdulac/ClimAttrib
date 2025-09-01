import hashlib, json, pickle, os
import redis

REDIS_TTL=60*60*48 # 48 hours caching

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=1
)


def make_cache_key(event: dict) -> str:
    payload = json.dumps(event, sort_keys=True, default=str).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def set_cache(cache_key: str, value, ttl: int = REDIS_TTL):
    redis_client.set(cache_key, pickle.dumps(value), ex=ttl)


def cache_exists(*args: list):
    return redis_client.exists(*args) == len(args)


def get_cache(cache_key: str, reset_ttl=REDIS_TTL):
    data = redis_client.get(cache_key)
    if data and reset_ttl:
        redis_client.expire(cache_key, reset_ttl)
    return pickle.loads(data) if data else None