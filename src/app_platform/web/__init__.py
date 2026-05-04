"""
Flask route registrations for the web layer.

- ``api/`` — public endpoints (GeoJSON tiles, CSV download); mounted under
  ``/api/``.
- ``admin/`` — protected endpoints (cache clear, process restart, Stan
  pre-compilation); mounted under ``/admin/``, all require a valid
  ``ADMIN_SECRET`` signature.
- ``redirects.py`` — URL rewriting rules applied at app startup.
"""

from .redirects import register_redirects
from .admin import register_admin_routes

__all__ = [
    "register_redirects",
    "register_admin_routes"
]