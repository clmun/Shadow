import math

# The dimensions of the shape SVG must match those in shadow_config.py
WIDTH = 100
HEIGHT = 100

def normalize_coords(coords, width=WIDTH, height=HEIGHT, eps=1e-9):
    """
    Transform a list of geographic coordinates (lat, lon)
    into a list of points (x, y) for SVG.
    """
    lats = [lat for lat, lon in coords]
    lons = [lon for lat, lon in coords]

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon

    points = []
    for lat, lon in coords:
        # Normalize based on longitude for x and latitude for y
        x = (lon - min_lon) / lon_range * width
        y = (lat - min_lat) / lat_range * height
        # Invert Y to match SVG coordinates (0 at the top)
        y = height - y
        points.append({"x": round(x, 2), "y": round(y, 2)})
    return points


if __name__ == "__main__":
    # Example: lat/lon coordinates for a shape
    coords = [
        (5.756524342539315, 4.147497678530097),   # point 1
        (5.75655147794478, 4.14758149755787),     # point 2
        (5.75653884598887, 4.14759155586402),     # point 3
        (5.75655662432034, 4.147641847306073),    # point 4
        (5.75646632918013, 4.147709573050665),    # point 5
        (5.7564195441265, 4.14757881552004)       # point 6
    ]

    shape = normalize_coords(coords)
    print("SHAPE = ", shape)
