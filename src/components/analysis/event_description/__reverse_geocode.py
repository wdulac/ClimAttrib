"""
Grid-cell reverse geocoding using a Natural Earth shapefile.

Loads ``data/ne_10_admin/ne_10m_admin_1_states_provinces.shp`` at module import
time. ``reverse_lookup(lat, lon, cell_size)`` builds a bounding box centred on the
given coordinates, finds all administrative regions that intersect it, and returns
the one with the largest intersection area as a dict with keys ``'country'``,
``'region'``, and ``'sub-region'``. Returns ``None`` for ocean or uncovered cells.
"""

import geopandas as gpd
from shapely.geometry import box
from app_platform.shared.paths import DATA

# Charger shapefile
gdf = gpd.read_file(DATA / "ne_10_admin/ne_10m_admin_1_states_provinces.shp")

def reverse_lookup(lat: float, lon: float, cell_size: float = 2.5):
    """
    Retourne le pays/région dominant dans une maille autour d'un centre (lat, lon).
    
    lat, lon : centre de la maille
    cell_size : taille en degrés (par défaut 2.5°)
    """
    # Construire la "maille" comme un rectangle centré sur (lon, lat)
    half = cell_size / 2
    grid_cell = box(lon - half, lat - half, lon + half, lat + half)

    # Trouver les entités qui intersectent cette maille
    candidates = gdf[gdf.intersects(grid_cell)].copy()
    if candidates.empty:
        return None

    # Calculer la surface d'intersection pour chacune
    candidates["intersection_area"] = candidates.intersection(grid_cell).area

    # Garder celle qui couvre la plus grande surface
    best = candidates.loc[candidates["intersection_area"].idxmax()]

    return {
        "country": best["admin"],
        "region": best["region"],
        "sub-region": best["name"]
    }