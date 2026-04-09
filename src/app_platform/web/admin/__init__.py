from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

from .register import register_admin_routes