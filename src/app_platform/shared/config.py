import os
from .paths import ROOT
from dotenv import load_dotenv

load_dotenv(ROOT / '.env', override=True)

APP_HOST=os.getenv('HOST', '127.0.0.1')
APP_PORT=int(os.getenv('PORT', '8000'))
APP_DEBUG=os.getenv('DEBUG', 'False').upper() == 'TRUE'
APP_SHOW_DASH_DEV_TOOLS=os.getenv('SHOW_DASH_DEV_TOOLS', 'False').upper() == 'TRUE'

_url_raw = os.getenv("URL_BASE_PATHNAME", "").strip("/")

# Cas racine
if not _url_raw:
    URL_PREFIX = ""               # pour concaténation
    URL_PREFIX_DASH = "/"         # pour Dash
else:
    URL_PREFIX = f"/{_url_raw}"       # "/eventtest"
    URL_PREFIX_DASH = f"/{_url_raw}/" # "/eventtest/"

PRODUCTION=os.getenv("PRODUCTION", "False").upper() == "TRUE"