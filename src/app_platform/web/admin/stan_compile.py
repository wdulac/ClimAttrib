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