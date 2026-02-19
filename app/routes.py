from flask import Blueprint, request, jsonify
from app.pireps import get_route_pireps
from app.atis import check_for_atis_change
from app.airports import get_airport, get_coords

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return "Preflight Intel hello world"


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