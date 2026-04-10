from flask import request, abort, jsonify
import os

from .__signature import verify_signature

from app_platform.web.admin import admin_bp

from app_platform.compute.celery import celery_app
from science.attribution.__settings import STAN_WORK_DIR


compilation_task = celery_app.tasks['compile_model']


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

    # Start a compilation celery task for each model that is absent
    for model in presence.keys():
        if not presence[model]:
            compilation_task.delay(model)

    return jsonify({
        'status': 'ok',
        'Models': {
            model: "Nothing to do" if presence[model] else "Compilation task sent"\
                for model in presence.keys()
        }
    })