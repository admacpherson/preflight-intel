import requests
from shapely.geometry import Point, Polygon, MultiPolygon
from config import Config


def fetch_sigmets() -> list[dict]:
    """Fetch all active SIGMETs and AIRMETs from AviationWeather.gov."""
    url = f"{Config.AVIATIONWEATHER_BASE_URL}/airsigmet"
    params = {
        "format": "json",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def parse_sigmet_polygon(sigmet: dict):
    """
    Extract a Shapely polygon from a SIGMET's coordinate data.
    Returns a Polygon or None if coordinates are missing/invalid.
    """
    try:
        coords = sigmet.get("coords", [])
        if not coords or len(coords) < 3:
            return None
        points = [(c["lon"], c["lat"]) for c in coords]
        return Polygon(points)
    except (KeyError, TypeError, ValueError):
        return None


def filter_sigmets_by_corridor(sigmets: list[dict], corridor) -> list[dict]:
    """Return only SIGMETs whose polygon intersects the route corridor."""
    filtered = []
    for sigmet in sigmets:
        polygon = parse_sigmet_polygon(sigmet)
        if polygon and polygon.is_valid and corridor.intersects(polygon):
            filtered.append(sigmet)
    return filtered


def get_route_sigmets(origin_coords: tuple, destination_coords: tuple) -> list[dict]:
    """
    Master function: return SIGMETs and AIRMETs that intersect the route corridor.
    """
    from app.corridor import build_corridor
    all_sigmets = fetch_sigmets()
    corridor = build_corridor(origin_coords, destination_coords)
    return filter_sigmets_by_corridor(all_sigmets, corridor)