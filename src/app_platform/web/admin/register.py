from app_platform.web.admin import admin_bp
from app_platform.shared.config import URL_PREFIX

# import pour enregistrer les routes
from app_platform.web.admin import clear_cache, restart, stan_compile


def register_admin_routes(server):
    server.register_blueprint(admin_bp, url_prefix=f"{URL_PREFIX}/admin")