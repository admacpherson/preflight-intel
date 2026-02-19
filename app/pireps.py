import requests
from shapely.geometry import Point
from config import Config
from app.corridor import build_corridor, compute_bbox

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


def filter_pireps_by_corridor(pireps: list[dict], corridor) -> list[dict]:
    filtered = []
    for pirep in pireps:
        try:
            lat = pirep["lat"]
            lon = pirep["lon"]
            point = Point(lon, lat)
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