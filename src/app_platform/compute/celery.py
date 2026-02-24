from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from science.attribution import attribute_event
from .redis import set_cache, make_cache_key

import app_platform.shared.config # So that celery workers load env variables from .env

import os

# Setting up Celery
celery_app = Celery(
    "tasks",
    broker=f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6380')}/0", # Redis for tasks queuing
    backend=None,
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["json", "pickle"],
    task_ignore_result=True
)

@celery_app.task(
    name="attribution",
    soft_time_limit=120, # 2 minutes. Expected run time for completion is ~20s
    time_limit=150
)
def attribution(event, cache_key=None):

    try:

        N_PROCESS = int(os.getenv('MCMC_N_WORKERS', 1))
        result = attribute_event(event, n_process=N_PROCESS)

        if not cache_key:
            cache_key = make_cache_key(event)

        set_cache(cache_key, {'status': 'ok', 'result': result})

    except SoftTimeLimitExceeded:

        if not cache_key:
            cache_key = make_cache_key(event)
        
        # Shorten the TTL to 5 seconds so that the DOA result does not stay in cache for 48 hours
        # But still long enough for the callback to see the timeout at least once
        set_cache(cache_key, {'status': 'timeout'}, ttl=5)
