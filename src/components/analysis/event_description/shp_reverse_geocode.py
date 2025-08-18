import geopandas as gpd
from shapely.geometry import Point

# Charger shapefile
gdf = gpd.read_file("data/ne_10_admin/ne_10m_admin_1_states_provinces.shp")

def reverse_lookup(lat, lon):
    point = Point(lon, lat)
    match = gdf[gdf.geometry.contains(point)]
    if match.empty:
        return None
    row = match.iloc[0]
    return {
        "country": row["admin"],
        "region": row["name"]
    }