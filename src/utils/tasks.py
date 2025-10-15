from celery import Celery
from science import attribute_event
from .redis_cache import set_cache, make_cache_key
import os

# Setting up Celery
celery_app = Celery(
    "tasks",
    broker=f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0", # Redis for tasks queuing
    backend=None,
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["json", "pickle"],
    task_ignore_result=True
)

@celery_app.task(name="attribution")
def attribution(event, cache_key=None):

    N_PROCESS = os.getenv('MCMC_N_WORKERS', 1)
    result = attribute_event(event, n_process=N_PROCESS)

    if not cache_key:
        cache_key = make_cache_key(event)

    set_cache(cache_key, result)

    return result