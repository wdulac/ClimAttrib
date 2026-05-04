"""
Admin endpoint: restart the application.

Route: ``POST {URL_PREFIX}/admin/restart``
Required headers: ``Timestamp``, ``Signature`` (see ``__signature.py``).

Performs a graceful restart in two steps:

1. Broadcasts a Celery ``shutdown`` control command to all workers.
2. Sends ``SIGHUP`` to the gunicorn master process, triggering a graceful worker
   reload without dropping in-flight requests.

Returns 403 if the signature is missing or invalid.
"""

from flask import request, abort, jsonify

from app_platform.web.admin import admin_bp
from app_platform.compute.celery import celery_app

from .__signature import verify_signature

import os
import signal
import psutil
    

@admin_bp.route("/restart", methods=["POST"])
def restart_app():

    timestamp = request.headers.get('Timestamp')
    signature = request.headers.get('Signature')

    if not all([timestamp, signature]):
        abort(403)

    if not verify_signature("restart", timestamp, signature):
        # Include route in payload to prevent reusing signature from another route
        abort(403)
    
    results = {}

    # 1. Extinction de celery
    try:
        celery_app.control.broadcast('shutdown', destination=None, reply=False) # Broadcast à tous les workers
        results["celery"] = "shutdown broadcast sent"
    except Exception as e:
        results["celery"] = f"error: {e}"

    # 2. Gunicorn : SIGHUP sur le process master ; on espère avoir le temps d'envoyer la réponse avant l'extinction
    try:
        current_pid = os.getpid()
        current_proc = psutil.Process(current_pid)
        # Remonter jusqu'au master gunicorn (parent du worker)
        master = current_proc.parent()
        os.kill(master.pid, signal.SIGHUP)
        results["gunicorn"] = f"SIGHUP sent to master PID {master.pid}"
    except Exception as e:
        results["gunicorn"] = f"error: {e}"

    return jsonify({"status": "ok", "results": results})