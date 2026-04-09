from flask import request, abort, jsonify
import os

from app_platform.web.admin import admin_bp
from app_platform.compute.redis import redis_client


ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

@admin_bp.route("/clear-cache", methods=["POST"])
def clear_redis_cache():
    
    token = request.headers.get("Admin-Token")

    if not token or token != ADMIN_TOKEN:
        abort(403)

    # Vider db 1 redis
    redis_client.flushdb()
    return jsonify({"status": "cache cleared"})