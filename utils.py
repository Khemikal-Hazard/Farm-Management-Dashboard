# utils.py

from shapely import wkt

# -------------------------------
# Parse WKT Geometry to Lat/Lon
# -------------------------------
def extract_lat_lon_from_wkt(geom_str: str):
    """
    Converts WKT point string to latitude and longitude.
    Returns (lat, lon) or (None, None) if invalid.
    """
    try:
        point = wkt.loads(geom_str)
        return point.y, point.x
    except Exception:
        return None, None