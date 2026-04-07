from app_platform.web.api import api_bp
from app_platform.shared.config import URL_PREFIX

# import pour enregistrer les routes
from app_platform.web.api import geojson_tiles  # noqa
from app_platform.web.api import download_csv   # noqa


def register_api_routes(server):

    from flask_compress import Compress

    server.config['COMPRESS_REGISTER'] = False
    Compress().init_app(server)

    server.register_blueprint(
        api_bp,
        url_prefix=f"{URL_PREFIX}/api"
    )