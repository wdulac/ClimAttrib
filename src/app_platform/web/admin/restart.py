import hmac, hashlib, time
from flask import request, abort, jsonify

from app_platform.web.admin import admin_bp
from app_platform.compute.celery import celery_app

import os
import signal
import psutil


ADMIN_SECRET = os.getenv("ADMIN_SECRET").encode('utf-8')
HASH = hashlib.sha256


def verify_signature(route, timestamp, signature, max_age=30):
    # Including route into the payload prevents reusing a signature from another route

    if abs(time.time() - int(timestamp)) > max_age:
        return False

    payload = f"{timestamp}:{route}".encode('utf-8')
    expected = hmac.new(ADMIN_SECRET, payload, HASH).hexdigest()
    
    return hmac.compare_digest(expected, signature)
    

@admin_bp.route("/restart", methods=["POST"])
def restart_app():

    timestamp = request.headers.get('Timestamp')
    signature = request.headers.get('Signature')

    if not all([timestamp, signature]):
        abort(403)

    if not verify_signature("restart", timestamp, signature):
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