import requests
from shapely.geometry import Point
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.corridor import build_corridor, compute_bbox, build_great_circle_line, calculate_distance_nm


def fetch_pireps(bbox: tuple, lookback_hours: int = None) -> list[dict]:
    """
    Fetch all recent PIREPs from AviationWeather.gov.
    bbox is (min_lat, min_lon, max_lat, max_lon)
    """
    url = f"{Config.AVIATIONWEATHER_BASE_URL}/pirep"
    params = {
        "format": "json",
        "age": lookback_hours or Config.PIREP_LOOKBACK_HOURS_SHORT,
        "level": Config.PIREP_ALTITUDE_LEVEL,
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    if not response.text.strip():
        return []

    return response.json()


def fetch_pireps_for_route(origin_coords: tuple, destination_coords: tuple, lookback_hours: int) -> list[dict]:
    """
    Split long routes into segments and fetch PIREPs for each,
    avoiding the API's 400 result cap on large bounding boxes.
    """
    distance_nm = calculate_distance_nm(origin_coords, destination_coords)

    # One segment per 1000nm, minimum 1
    num_segments = max(1, int(distance_nm / 500))

    if num_segments == 1:
        bbox = compute_bbox(origin_coords, destination_coords)
        return fetch_pireps(bbox, lookback_hours=lookback_hours)

    # Generate segment waypoints along the great circle
    line = build_great_circle_line(origin_coords, destination_coords)
    total_points = len(line.coords)
    points = list(line.coords)  # (lon, lat)

    # Split points into segments
    segment_size = total_points // num_segments
    all_pireps = []
    seen_ids = set()

    def fetch_segment(i):
        start_idx = i * segment_size
        end_idx = start_idx + segment_size + 1 if i < num_segments - 1 else total_points
        segment_points = points[start_idx:end_idx]
        seg_origin = (segment_points[0][1], segment_points[0][0])
        seg_dest = (segment_points[-1][1], segment_points[-1][0])
        avg_lat = (seg_origin[0] + seg_dest[0]) / 2
        padding = 3.0 if avg_lat < 50 else 1.5
        bbox = compute_bbox(seg_origin, seg_dest, padding_deg=padding)
        return fetch_pireps(bbox, lookback_hours=lookback_hours)

    all_pireps = []
    seen_ids = set()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_segment, i): i for i in range(num_segments)}
        for future in as_completed(futures):
            try:
                segment_pireps = future.result()
                for p in segment_pireps:
                    key = (p.get("receiptTime"), p.get("icaoId"))
                    if key not in seen_ids:
                        seen_ids.add(key)
                        all_pireps.append(p)
            except Exception:
                continue

    return all_pireps


def filter_pireps_by_corridor(pireps: list[dict], corridor) -> list[dict]:
    filtered = []
    for pirep in pireps:
        try:
            # Exclude ACARS position reports
            if pirep.get("pirepType") in ("ARP", "AIREP"):
                continue

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

    # Calculate distance lookback window
    distance_nm = calculate_distance_nm(origin_coords, destination_coords)
    lookback = Config.PIREP_LOOKBACK_HOURS_LONG if distance_nm > Config.MD_DISTANCE else Config.PIREP_LOOKBACK_HOURS_MED if distance_nm > Config.SH_DISTANCE else Config.PIREP_LOOKBACK_HOURS_SHORT

    all_pireps = fetch_pireps_for_route(origin_coords, destination_coords, lookback_hours=lookback)
    corridor = build_corridor(origin_coords, destination_coords)
    return filter_pireps_by_corridor(all_pireps, corridor)