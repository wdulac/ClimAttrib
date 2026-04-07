from flask import Blueprint

api_bp = Blueprint("api", __name__)

from .register import register_api_routes