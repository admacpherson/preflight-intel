import pytest
from app.pireps import compute_bbox, build_corridor, filter_pireps_by_corridor

# Sample airports
KORD = (41.97, -87.90)
KDEN = (39.85, -104.67)

def test_compute_bbox_ordering():
    bbox = compute_bbox(KORD, KDEN)
    assert bbox[0] < bbox[2]   # min_lat < max_lat
    assert bbox[1] < bbox[3]   # min_lon < max_lon

def test_compute_bbox_contains_both_airports():
    bbox = compute_bbox(KORD, KDEN)
    assert bbox[0] <= KORD[0] <= bbox[2]
    assert bbox[0] <= KDEN[0] <= bbox[2]

def test_corridor_contains_midpoint():
    corridor = build_corridor(KORD, KDEN)
    mid_lat = (KORD[0] + KDEN[0]) / 2
    mid_lon = (KORD[1] + KDEN[1]) / 2
    from shapely.geometry import Point
    assert corridor.contains(Point(mid_lon, mid_lat))

def test_filter_removes_out_of_corridor_pireps():
    from shapely.geometry import Point
    corridor = build_corridor(KORD, KDEN)
    fake_pireps = [
        {"lat": 40.9, "lon": -96.0},
        {"lat": 25.0, "lon": -80.0},
        {"lat": 48.0, "lon": -122.0},
    ]
    results = filter_pireps_by_corridor(fake_pireps, corridor)
    assert len(results) == 1
    assert results[0]["lon"] == -96.0