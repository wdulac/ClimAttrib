import os
from .paths import ROOT
from dotenv import load_dotenv

load_dotenv(ROOT / '.env')

APP_HOST=os.getenv('HOST')
APP_PORT=int(os.getenv('PORT'))
APP_DEBUG=os.getenv('DEBUG').upper() == 'TRUE'
APP_SHOW_DASH_DEV_TOOLS=os.getenv('SHOW_DASH_DEV_TOOLS').upper() == 'TRUE'