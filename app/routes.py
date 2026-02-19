from flask import Blueprint, request, jsonify, render_template
from app.pireps import get_route_pireps
from app.atis import check_for_atis_change
from app.airports import get_airport, get_coords
import folium
from io import BytesIO
from app.airports import get_coords

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/api/pireps")
def pireps():
    """
    GET /api/pireps?origin=KORD&destination=KDEN
    Returns PIREPs filtered to the route corridor.
    """
    origin = request.args.get("origin", "").upper()
    destination = request.args.get("destination", "").upper()

    if not origin or not destination:
        return jsonify({"error": "origin and destination are required"}), 400

    origin_coords = get_coords(origin)
    destination_coords = get_coords(destination)

    if not origin_coords:
        return jsonify({"error": f"Airport not found: {origin}"}), 404
    if not destination_coords:
        return jsonify({"error": f"Airport not found: {destination}"}), 404

    airport_coords = {origin: origin_coords, destination: destination_coords}
    results = get_route_pireps(origin, destination, airport_coords)

    return jsonify({
        "origin": origin,
        "destination": destination,
        "count": len(results),
        "pireps": results
    })


@main.route("/api/atis")
def atis():
    """
    GET /api/atis?airports=KORD,KDEN
    Returns ATIS change status for one or more airports.
    """
    airports_param = request.args.get("airports", "")
    if not airports_param:
        return jsonify({"error": "airports parameter is required"}), 400

    icao_list = [a.strip().upper() for a in airports_param.split(",")]
    results = []
    for icao in icao_list:
        airport = get_airport(icao)
        if not airport:
            results.append({"airport": icao, "error": "Airport not found"})
            continue
        status = check_for_atis_change(icao)
        results.append(status)

    return jsonify({"airports": results})

@main.route("/api/map")
def map_view():
    origin = request.args.get("origin", "").upper()
    destination = request.args.get("destination", "").upper()

    origin_coords = get_coords(origin)
    destination_coords = get_coords(destination)

    if not origin_coords or not destination_coords:
        return "Airport not found", 404

    mid_lat = (origin_coords[0] + destination_coords[0]) / 2
    mid_lon = (origin_coords[1] + destination_coords[1]) / 2

    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=5, tiles="CartoDB dark_matter")

    folium.Marker(origin_coords, tooltip=origin, icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(destination_coords, tooltip=destination, icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine([origin_coords, destination_coords], color="#00d4ff", weight=2, opacity=0.7).add_to(m)

    return m._repr_html_()