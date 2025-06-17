from app import server
import os
import json
from flask import request, jsonify


@server.route("/grid_tiles")
def serve_grid_tiles():
    bounds_str = request.args.get("bounds", None)
    if bounds_str is None:
        return jsonify({"type": "FeatureCollection", "features": []})

    # bounds: [[south, west], [north, east]]
    bounds = json.loads(bounds_str)
    south, west = bounds[0]
    north, east = bounds[1]

    TILE_SIZE = 10
    def tile_indices_in_bbox(south, west, north, east):
        x_min = int(west // TILE_SIZE)
        x_max = int(east // TILE_SIZE)
        y_min = int(south // TILE_SIZE)
        y_max = int(north // TILE_SIZE)
        return [(x, y) for x in range(x_min, x_max + 1) for y in range(y_min, y_max + 1)]

    features = []
    for x, y in tile_indices_in_bbox(south, west, north, east):
        tile_path = f"src/assets/static/grid_tiles/tile_{x}_{y}.geojson"
        if os.path.exists(tile_path):
            with open(tile_path, "r") as f:
                tile_data = json.load(f)
                features.extend(tile_data["features"])

    return jsonify({"type": "FeatureCollection", "features": features})
