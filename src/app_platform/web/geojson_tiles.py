import os
import json

from flask import request, jsonify
from flask_compress import Compress
from functools import lru_cache

from app_platform.shared.paths import ASSETS
from app_platform.shared.config import URL_PREFIX


TILE_SIZE =10
GRID_TILES_DIR = ASSETS / "static/grid_tiles/"

@lru_cache(maxsize=128)
def load_tile(x, y):
    tile_path = os.path.join(GRID_TILES_DIR, f"tile_{x}_{y}.geojson")
    if os.path.exists(tile_path):
        with open(tile_path, "r") as f:
            tile_data = json.load(f)
            return tile_data["features"]
    return []


def tile_indices_in_bbox(south, west, north, east):
    x_min = int(west // TILE_SIZE)
    x_max = int(east // TILE_SIZE)
    y_min = int(south // TILE_SIZE)
    y_max = int(north // TILE_SIZE)
    return [(x, y) for x in range(x_min, x_max + 1) for y in range(y_min, y_max + 1)]

def register_geojson_routes(server):

    server.config['COMPRESS_REGISTER'] = False # Disable default compression
    compress = Compress()
    compress.init_app(server)

    @server.route(f"{URL_PREFIX}/grid_tiles")
    @compress.compressed()
    def serve_grid_tiles():
        bounds_str = request.args.get("bounds", None)
        if bounds_str is None:
            return jsonify({"type": "FeatureCollection", "features": []})

        # bounds: [[south, west], [north, east]]
        bounds = json.loads(bounds_str)
        south, west = bounds[0]
        north, east = bounds[1]

        features = []
        for x, y in tile_indices_in_bbox(south, west, north, east):
            features.extend(load_tile(x, y))

        return jsonify({"type": "FeatureCollection", "features": features})
