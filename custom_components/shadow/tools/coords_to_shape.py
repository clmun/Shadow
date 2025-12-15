import math

# --- Here you have to put your coordinates (lat, lon)---
coords = [
    (45.75672246183737, 24.14507467947945),
    (45.75633213234665, 24.145332882810937),
    (45.756201858743545, 24.144919772449043),
    (45.756314563258954, 24.14483900499283),
    (45.75638919203197, 24.145094404451115),
    (45.75666943039342, 24.144902308510726)
]


def normalize_points(coords, width=100, height=100, rotate=True, angle_deg=0, margin=5):
    lat0 = sum(lat for lat, lon in coords) / len(coords)
    lon0 = sum(lon for lat, lon in coords) / len(coords)

    def to_xy(lat, lon):
        dx = (lon - lon0) * 111320 * math.cos(math.radians(lat0))
        dy = -(lat - lat0) * 110540   # flip pe Y
        return dx, dy

    points = [to_xy(lat, lon) for lat, lon in coords]

    if rotate:
        angle = math.radians(angle_deg)
        rotated = []
        for x, y in points:
            xr = x * math.cos(angle) - y * math.sin(angle)
            yr = x * math.sin(angle) + y * math.cos(angle)
            rotated.append((xr, yr))
        points = rotated

    xs, ys = zip(*points)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # scalare best fit în cerc
    radius = width/2 - margin
    diag = math.sqrt((max_x - min_x)**2 + (max_y - min_y)**2)
    scale = (radius * math.sqrt(2)) / diag

    # scalare + centrare
    norm_points = [
        {
            'x': (x - (min_x + max_x)/2) * scale + width/2,
            'y': (y - (min_y + max_y)/2) * scale + height/2
        }
        for x, y in points
    ]

    return norm_points

shape = normalize_points(coords, width=100, height=100, rotate=True, angle_deg=0)

# --- Write shadow_config.py ---
with open("shadow_config.py", "w") as f:
    f.write("WIDTH = 100\n")
    f.write("HEIGHT = 100\n\n")
    f.write("PRIMARY_COLOR = 'red'        #'#1b3024'\n")
    f.write("LIGHT_COLOR = '#26bf75'\n")
    f.write("BG_COLOR = '#1a1919'\n")
    f.write("SUN_COLOR = '#ffff66'\n")
    f.write("MOON_COLOR = '#999999'\n\n")
    f.write("SUN_RADIUS = 5\n")
    f.write("MOON_RADIUS = 3\n\n")
    f.write("# Shape of the house (original)\n")
    f.write("SHAPE = [\n")
    for p in shape:
        f.write(f"    {{'x': {p['x']:.2f}, 'y': {p['y']:.2f}}},\n")
    f.write("]\n")

print("Image shape.svg created in current folder. Check it.")
print("File shadow_config.py was generated in current folder. You have to copy it to custom_components/shadow/ folder.")