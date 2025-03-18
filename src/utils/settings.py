import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

APP_HOST=os.getenv('HOST')
APP_PORT=int(os.getenv('PORT'))
APP_DEBUG=os.getenv('DEBUG').upper() == 'TRUE'
APP_SHOW_DASH_DEV_TOOLS=os.getenv('SHOW_DASH_DEV_TOOLS').upper() == 'TRUE'