import os
from .paths import ROOT
from dotenv import load_dotenv

load_dotenv(ROOT / '.env')

APP_HOST=os.getenv('HOST', '127.0.0.1')
APP_PORT=int(os.getenv('PORT', '8000'))
APP_DEBUG=os.getenv('DEBUG', 'False').upper() == 'TRUE'
APP_SHOW_DASH_DEV_TOOLS=os.getenv('SHOW_DASH_DEV_TOOLS', 'False').upper() == 'TRUE'