"""
Admin endpoint: clear the Redis result cache.

Route: ``POST {URL_PREFIX}/admin/clear-cache``
Required headers: ``Timestamp``, ``Signature`` (see ``__signature.py``).

Flushes all entries in Redis DB 1 (the attribution result cache). Does not affect
the Celery task queue in DB 0. Returns 403 if the signature is missing or invalid.
"""

from flask import request, abort, jsonify

from app_platform.web.admin import admin_bp
from app_platform.compute.redis import redis_client

from .__signature import verify_signature


@admin_bp.route("/clear-cache", methods=["POST"])
def clear_redis_cache():
    
    timestamp = request.headers.get('Timestamp')
    signature = request.headers.get('Signature')

    if not all([timestamp, signature]):
        abort(403)
    
    if not verify_signature("clear-cache", timestamp, signature):
        # Include route in payload to prevent reusing signature from another route
        abort(403)

    # Vider db 1 redis
    redis_client.flushdb()
    return jsonify({"status": "ok", "redis": "cache cleared"})