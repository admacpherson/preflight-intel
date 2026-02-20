import pyproj
from shapely.geometry import Point, LineString
from shapely.ops import transform
from config import Config


def compute_bbox(origin: tuple, destination: tuple, padding_deg: float = 1.0) -> tuple:
    """
    Compute a bounding box that encompasses the full great circle path with padding.
    """
    line = build_great_circle_line(origin, destination)
    lons, lats = zip(*line.coords)

    min_lat = min(lats) - padding_deg
    max_lat = max(lats) + padding_deg
    min_lon = min(lons) - padding_deg
    max_lon = max(lons) + padding_deg
    return (min_lat, min_lon, max_lat, max_lon)


def build_great_circle_line(origin: tuple, destination: tuple, num_points: int = 100) -> LineString:
    """
    Generate a LineString following the great circle path between two points.
    origin and destination are (lat, lon) tuples.
    num_points controls how smooth the arc is.
    """
    geod = pyproj.Geod(ellps="WGS84")

    # npts returns intermediate points, not including start/end
    intermediate = geod.npts(
        origin[1], origin[0],           # lon, lat
        destination[1], destination[0],
        num_points - 2
    )

    # Build full point list: origin + intermediates + destination
    points = (
        [(origin[1], origin[0])] +
        [(lon, lat) for lon, lat in intermediate] +
        [(destination[1], destination[0])]
    )

    return LineString(points)


def build_corridor(origin: tuple, destination: tuple, width_nm: float = Config.CORRIDOR_WIDTH_NM):
    """
    Build a buffered corridor around a great circle route.
    origin and destination are (lat, lon) tuples.
    width_nm is the buffer width in nautical miles on each side.
    """
    # Convert nautical miles to meters (1nm = 1852m)
    width_m = width_nm * 1852

    # Draw a line between airport coords
    line = build_great_circle_line(origin, destination)

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