"""
Celery application and background task definitions.

Configures a Celery instance using Redis DB 0 as its task broker. Defines two tasks:

- ``attribution`` — the main computation task. Calls ``attribute_event()`` from
  ``science.attribution``, stores the result in the Redis cache (DB 1) under the
  event's cache key. Applies a 2-minute soft time limit and a 2.5-minute hard limit.
  On soft timeout, writes a ``{'status': 'timeout'}`` sentinel to the cache with a
  5-second TTL so the polling callback on the analysis page can detect and report
  the failure.

- ``compilation`` — compiles a Stan model (GEV or Normal) using the ANKIALE library.
  Dispatched by the admin ``/stan-compile`` endpoint; chained so both models compile
  sequentially on a single worker when both are missing.

The ``celery_app`` object is imported by ``pages/analysis.py`` to retrieve and queue
the ``attribution`` task.
"""

import app_platform.shared.config # So that celery workers load env variables from .env

from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
from science.attribution import attribute_event
from .redis import set_cache, make_cache_key

from science.attribution.__settings import STAN_WORK_DIR
from ANKIALE.stats.__tools import nslawid_to_class

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


@celery_app.task(
    name="compilation"
)
def compile_stan_model(model):

    # Map input parameter to proper nslawid
    nslawid = {"GEV": "GEV", "NORMAL": "Normal"}[model]
    cnslaw = nslawid_to_class(nslawid)

    # Start compilation
    cnslaw().init_stan(tmp=STAN_WORK_DIR, force_compile=True)