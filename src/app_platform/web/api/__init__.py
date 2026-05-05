"""
Flask Blueprint for public API endpoints.

Routes serve map tile data (GeoJSON) and attribution results (CSV download).
The Blueprint is registered on the Flask app by ``register_api_routes`` defined
in ``src/app_platform/web/api/register.py`` and called from ``app.py``.
"""

from flask import Blueprint

api_bp = Blueprint("api", __name__)

from .register import register_api_routes