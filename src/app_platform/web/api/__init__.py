"""
Flask Blueprint for public API endpoints.

Routes serve map tile data (GeoJSON) and attribution results (CSV download).
The Blueprint is registered on the Flask app by ``register_api_routes``
(called from ``web/__init__.py``).
"""

from flask import Blueprint

api_bp = Blueprint("api", __name__)

from .register import register_api_routes