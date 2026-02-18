from .redirects import register_redirects
from .geojson_tiles import register_geojson_routes
from .download_csv import register_download_routes

__all__ = [
    "register_redirects",
    "register_geojson_routes",
    "register_download_routes",
]