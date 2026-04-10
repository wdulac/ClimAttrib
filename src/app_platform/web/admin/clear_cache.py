import hmac, hashlib, time
from flask import request, abort, jsonify
import os

from app_platform.web.admin import admin_bp
from app_platform.compute.redis import redis_client


ADMIN_SECRET = os.getenv("ADMIN_SECRET").encode('utf-8')
HASH = hashlib.sha256


def verify_signature(route, timestamp, signature, max_age=30):
    # Including route into the payload prevents reusing a signature from another route

    if abs(time.time() - int(timestamp)) > max_age:
        return False

    payload = f"{timestamp}:{route}".encode('utf-8')
    expected = hmac.new(ADMIN_SECRET, payload, HASH).hexdigest()

    return hmac.compare_digest(expected, signature)


@admin_bp.route("/clear-cache", methods=["POST"])
def clear_redis_cache():
    
    timestamp = request.headers.get('Timestamp')
    signature = request.headers.get('Signature')

    if not all([timestamp, signature]):
        abort(403)
    
    if not verify_signature("clear-cache", timestamp, signature):
        abort(403)

    # Vider db 1 redis
    redis_client.flushdb()
    return jsonify({"status": "ok", "redis": "cache cleared"})