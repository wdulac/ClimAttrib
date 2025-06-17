#!/bin/env python3

import json
import math
import os

TILE_SIZE = 10  # degress
INPUT = "../src/assets/static/grid_1_5.geojson"
OUTPUT_DIR = "../src/assets/static/grid_tiles"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT, "r") as f:
    geojson = json.load(f)

tiles = {}

for feature in geojson["features"]:
    lon, lat = feature["geometry"]["coordinates"][0][0]
    tile_x = int(math.floor(lon / TILE_SIZE))
    tile_y = int(math.floor(lat / TILE_SIZE))
    key = f"{tile_x}_{tile_y}"
    tiles.setdefault(key, []).append(feature)

for key, feats in tiles.items():
    tile_geojson = {
        "type": "FeatureCollection",
        "features": feats
    }
    with open(os.path.join(OUTPUT_DIR, f"tile_{key}.geojson"), "w") as f:
        json.dump(tile_geojson, f)
