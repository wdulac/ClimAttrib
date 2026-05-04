"""
Runtime configuration loader.

Loads the ``.env`` file from the project root (via ``python-dotenv``) and exports
typed settings used across the application:

- ``APP_HOST``, ``APP_PORT``, ``APP_DEBUG`` — Flask/Dash server binding parameters.
- ``APP_SHOW_DASH_DEV_TOOLS`` — enables Dash's hot-reload overlay and debug panel.
- ``URL_PREFIX`` — URL path prefix for all routes (e.g. ``/eventtest``), empty string
  when the app is served at the root.
- ``URL_PREFIX_DASH`` — same prefix formatted for Dash's ``url_base_pathname``
  (always ends with ``/``).
- ``PRODUCTION`` — when True, enables the ProxyFix WSGI middleware in ``app.py``
  to correctly handle headers set by a reverse proxy.

This module must be imported early. Celery workers import it as their first import
so that ``.env`` variables are loaded before any other module reads ``os.getenv``.
"""

import os
from .paths import ROOT
from dotenv import load_dotenv

load_dotenv(ROOT / '.env', override=True)

APP_HOST=os.getenv('HOST', '127.0.0.1')
APP_PORT=int(os.getenv('PORT', '8000'))
APP_DEBUG=os.getenv('DEBUG', 'False').upper() == 'TRUE'
APP_SHOW_DASH_DEV_TOOLS=os.getenv('SHOW_DASH_DEV_TOOLS', 'False').upper() == 'TRUE'

_url_raw = os.getenv("URL_PREFIX", "").strip("/")

# Cas racine
if not _url_raw:
    URL_PREFIX = ""               # pour concaténation
    URL_PREFIX_DASH = "/"         # pour Dash
else:
    URL_PREFIX = f"/{_url_raw}"       # "/eventtest"
    URL_PREFIX_DASH = f"/{_url_raw}/" # "/eventtest/"

PRODUCTION=os.getenv("PRODUCTION", "False").upper() == "TRUE"