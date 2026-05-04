"""
Flask Blueprint for protected admin endpoints.

All routes defined here require a valid ``ADMIN_SECRET`` HMAC signature
(checked by ``__signature.py``). The Blueprint is registered on the Flask app
by ``register_admin_routes`` (called from ``web/__init__.py``).
"""

from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

from .register import register_admin_routes