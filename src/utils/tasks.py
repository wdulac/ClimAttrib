from celery import Celery
from science import attribute_event
from .redis_cache import set_cache
import os

# Setting up Celery
celery_app = Celery(
    "tasks",
    broker=f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0", # Redis for tasks queuing
    backend=f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0", # Redis for passing/storing results
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["json", "pickle"]
)

@celery_app.task(name="attribution")
def attribution(event, cache_key=None):
    
    result = attribute_event(event)

    if cache_key:
        set_cache(cache_key, result, ttl=60*60*24)

    return result