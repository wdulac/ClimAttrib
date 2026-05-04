"""
Admin endpoint: pre-compile Stan statistical models.

Route: ``POST {URL_PREFIX}/admin/stan-compile``
Required headers: ``Timestamp``, ``Signature`` (see ``__signature.py``).

Checks which Stan model binaries (GEV, Normal) are absent from ``STAN_WORK_DIR``
and queues Celery ``compilation`` tasks for the missing ones. When both need
compiling, uses a Celery chain to run them sequentially on the same worker, avoiding
the memory spike of two simultaneous compilations. Returns 403 if the signature is
missing or invalid.

Stan models must be compiled before the ``attribution`` task can run. On a fresh
deployment, call this endpoint once before allowing user traffic.
"""

from flask import request, abort, jsonify
import os

from .__signature import verify_signature

from app_platform.web.admin import admin_bp

from app_platform.compute.celery import celery_app
from celery import chain
from science.attribution.__settings import STAN_WORK_DIR


compilation_task = celery_app.tasks['compilation']


@admin_bp.route("/stan-compile", methods=["POST"])
def compile_stan_models():

    timestamp = request.headers.get('Timestamp')
    signature = request.headers.get('Signature')

    if not all([timestamp, signature]):
        abort(403)

    if not verify_signature("stan-compile", timestamp, signature):
        abort(403)

    # Check presence of compiled stan models
    presence = {
        "GEV": False,
        "NORMAL": False
    }

    models = [_ for _ in os.listdir(STAN_WORK_DIR) if _.startswith('STAN_') \
              and not _.endswith('.stan')]

    for m in models:
        _m = m.split('_')[1].replace('MODEL', '')
        presence[_m] = True

    models_to_compile = [model for model, present in presence.items() if not present]

    if len(models_to_compile) == 2:
        # Use a celery chain to send both compilations to a single worker, to avoid maxing out memory
        chain(
            compilation_task.si(models_to_compile[0]),
            compilation_task.si(models_to_compile[1])
        ).delay()
    elif len(models_to_compile) == 1:
        compilation_task.delay(models_to_compile[0])

    return jsonify({
        'status': 'ok',
        'Models': {
            model: "Nothing to do" if presence[model] else "Compilation task sent"\
                for model in presence.keys()
        }
    })