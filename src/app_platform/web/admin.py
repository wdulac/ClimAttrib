from flask import Blueprint, request, jsonify, abort
import os

from app_platform.shared.config import URL_PREFIX
from app_platform.compute.redis import redis_client

admin_bp = Blueprint("admin", __name__)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

@admin_bp.route("/clear-cache", methods=["POST"])
def clear_redis_cache():
    
    token = request.headers.get("Admin-Token")

    if not token or token != ADMIN_TOKEN:
        abort(403)

    # Vider db 1 redis
    redis_client.flushdb()
    return jsonify({"status": "cache cleared"})

    
def register_admin_routes(server):
    server.register_blueprint(admin_bp, url_prefix=f"{URL_PREFIX}/admin")