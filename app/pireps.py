import requests
import pyproj
from shapely.geometry import Point, LineString
from shapely.ops import transform
from config import Config

def fetch_pireps(bbox: tuple) -> list[dict]:
    """
    Fetch all recent PIREPs from AviationWeather.gov.
    bbox is (min_lat, min_lon, max_lat, max_lon)
    """
    url = f"{Config.AVIATIONWEATHER_BASE_URL}/pirep"
    params = {
        "format": "json",
        "age": Config.PIREP_LOOKBACK_HOURS,
        "level": Config.PIREP_ALTITUDE_LEVEL,
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def compute_bbox(origin: tuple, destination: tuple, padding_deg: float = 1.0) -> tuple:
    """
    Compute a bounding box that encompasses both airports with padding.
    Returns (min_lat, min_lon, max_lat, max_lon)
    """
    min_lat = min(origin[0], destination[0]) - padding_deg
    max_lat = max(origin[0], destination[0]) + padding_deg
    min_lon = min(origin[1], destination[1]) - padding_deg
    max_lon = max(origin[1], destination[1]) + padding_deg
    return (min_lat, min_lon, max_lat, max_lon)


def build_corridor(origin: tuple, destination: tuple, width_nm: float = Config.CORRIDOR_WIDTH_NM):
    """
    Build a buffered corridor around a great circle route.
    origin and destination are (lat, lon) tuples.
    width_nm is the buffer width in nautical miles on each side.
    """
    # Convert nautical miles to meters (1nm = 1852m)
    width_m = width_nm * 1852

    # Draw a line between airport coords
    line = LineString([
        (origin[1], origin[0]),           # Shapely uses (lon, lat)
        (destination[1], destination[0])
    ])

    # Project to a meter-based CRS for accurate buffering
    wgs84 = pyproj.CRS("EPSG:4326")     # Standard long/lat from API
    mercator = pyproj.CRS("EPSG:3857")  # Convert to meters in Web Mercator projection
    project = pyproj.Transformer.from_crs(wgs84, mercator, always_xy=True).transform    # Transform wgs to mercator
    rev_project = pyproj.Transformer.from_crs(mercator, wgs84, always_xy=True).transform  # Reverse transform mercator to wgs

    # Transform line string between airports into corridor
    line_projected = transform(project, line)
    corridor_projected = line_projected.buffer(width_m)
    corridor = transform(rev_project, corridor_projected)

    return corridor


def filter_pireps_by_corridor(pireps: list[dict], corridor) -> list[dict]:
    """Return only PIREPs whose location falls within the corridor."""
    filtered = []
    for pirep in pireps:
        try:
            lat = pirep["latitude"]
            lon = pirep["longitude"]
            point = Point(lon, lat)   # Shapely uses (lon, lat)
            if corridor.contains(point):
                filtered.append(pirep)
        except (KeyError, TypeError):
            continue
    return filtered


def get_route_pireps(origin_icao: str, destination_icao: str, airport_coords: dict) -> list[dict]:
    """
    Master function: given two ICAO codes, return filtered PIREPs along the route.
    airport_coords should be a dict like {"KORD": (41.97, -87.90), "KDEN": (39.85, -104.67)}
    """
    origin_coords = airport_coords.get(origin_icao)
    destination_coords = airport_coords.get(destination_icao)

    if not origin_coords or not destination_coords:
        raise ValueError(f"Coordinates not found for one or both airports.")

    bbox = compute_bbox(origin_coords, destination_coords)
    all_pireps = fetch_pireps(bbox)
    corridor = build_corridor(origin_coords, destination_coords)
    return filter_pireps_by_corridor(all_pireps, corridor)