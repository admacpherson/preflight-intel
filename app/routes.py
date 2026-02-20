from flask import Blueprint, request, jsonify, render_template
from app.atis import check_for_atis_change
from app.airports import get_airport, get_coords
from app.pireps import get_route_pireps
from app.sigmets import get_route_sigmets, parse_sigmet_polygon
from app.corridor import build_great_circle_line
import folium

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

def pirep_marker_color(pirep: dict) -> str:
    """Return a color based on the most significant condition reported."""
    turb = pirep.get("tbInt1", "")
    ice = pirep.get("icgInt1", "")

    if turb in ("SEV", "EXTRM"):
        return "#ff0000"   # Red — severe turbulence
    if turb in ("MOD", "MOD-SEV"):
        return "#ff6b00"   # Orange — moderate turbulence
    if ice in ("SEV", "HVY"):
        return "#ff0000"   # Red — severe icing
    if ice in ("MOD",):
        return "#00aaff"   # Blue — moderate icing
    if turb in ("LGT", "LGT-MOD"):
        return "#ffff00"   # Yellow — light turbulence
    return "#00ff88"       # Green — nothing significant


def build_pirep_tooltip(pirep: dict) -> str:
    """Build a readable tooltip string for a PIREP marker."""
    parts = []
    ac = pirep.get("acType", "")
    alt = pirep.get("fltLvl")
    turb = pirep.get("tbInt1", "")
    ice = pirep.get("icgInt1", "")
    raw = pirep.get("rawOb", "")

    if ac:
        parts.append(f"A/C: {ac}")
    if alt:
        parts.append(f"Alt: FL{str(alt).zfill(3)}")
    if turb:
        parts.append(f"Turb: {turb}")
    if ice:
        parts.append(f"Ice: {ice}")
    parts.append(raw)

    return " | ".join(parts)

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

    # Route line
    gc_line = build_great_circle_line(origin_coords, destination_coords)
    gc_coords = [[lat, lon] for lon, lat in gc_line.coords]  # Folium uses [lat, lon]
    folium.PolyLine(gc_coords, color="#00d4ff", weight=2, opacity=0.7).add_to(m)

    # Airport markers
    folium.Marker(origin_coords, tooltip=origin, icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(destination_coords, tooltip=destination, icon=folium.Icon(color="red")).add_to(m)

    # PIREPs
    try:
        airport_coords = {origin: origin_coords, destination: destination_coords}
        pireps = get_route_pireps(origin, destination, airport_coords)
        for p in pireps:
            color = pirep_marker_color(p)
            tooltip = build_pirep_tooltip(p)
            tooltip_html = f"""
                        <div style="font-family:monospace; font-size:12px; line-height:1.8;">
                            <div style="color:#00d4ff; margin-bottom:4px;">{p.get('pirepType', 'PIREP')} — {p.get('acType', 'Unknown A/C')}</div>
                            <div>Alt: FL{str(p.get('fltLvl', '???')).zfill(3)}</div>
                            {'<div>Turbulence: ' + p.get('tbInt1') + '</div>' if p.get('tbInt1') else ''}
                            {'<div>Icing: ' + p.get('icgInt1') + ' ' + p.get('icgType1', '') + '</div>' if p.get('icgInt1') else ''}
                            {'<div>Temp: ' + str(p.get('temp')) + '°C</div>' if p.get('temp') is not None else ''}
                            <div style="color:#888; margin-top:4px; font-size:11px;">{p.get('rawOb', '')}</div>
                        </div>
                        """
            folium.CircleMarker(
                location=[p["lat"], p["lon"]],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                tooltip=folium.Tooltip(tooltip_html, sticky=True, direction="top")
            ).add_to(m)
    except Exception as e:
        pass  # Don't let PIREP errors break the map

    # SIGMETs
    try:
        sigmets = get_route_sigmets(origin_coords, destination_coords)
        for s in sigmets:
            polygon = parse_sigmet_polygon(s)
            if not polygon:
                continue
            hazard = s.get("hazard", "")
            color = "#ff0000" if hazard == "CONVECTIVE" else \
                "#00aaff" if hazard == "ICING" else "#ff6b00"
            coords = [[c["lat"], c["lon"]] for c in s.get("coords", [])]
            folium.Polygon(
                locations=coords,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.2,
                weight=2,
                tooltip=folium.Tooltip(
                    f"<div style='font-family:monospace;font-size:12px;'>"
                    f"<div style='color:#00d4ff'>{s.get('airSigmetType')} — {hazard}</div>"
                    f"<div>Series: {s.get('seriesId', '?')}</div>"
                    f"<div>Tops: FL{str(s.get('altitudeHi1', 0) // 100).zfill(3)}</div>"
                    f"<div>Movement: {s.get('movementDir', '?')}° at {s.get('movementSpd', '?')}kt</div>"
                    f"</div>",
                    sticky=True,
                    direction="top"
                )
            ).add_to(m)
    except Exception:
        pass

    # Add legend for PIREPS/SIGMET markers
    legend_html = """
        <div style="
            position: fixed;
            bottom: 24px;
            left: 24px;
            z-index: 1000;
            font-family: monospace;
            font-size: 12px;
        ">
            <input type="checkbox" id="legend-toggle" checked
                style="display:none;">
            <label for="legend-toggle" style="
                display: block;
                background: rgba(22, 33, 62, 0.95);
                border: 1px solid #0f3460;
                border-radius: 4px 4px 0 0;
                padding: 6px 12px;
                color: #00d4ff;
                cursor: pointer;
                letter-spacing: 1px;
                text-align: right;
                user-select: none;
            ">LEGEND</label>
            <div id="legend-body" style="
                background: rgba(22, 33, 62, 0.95);
                border: 1px solid #0f3460;
                border-top: none;
                border-radius: 0 0 4px 4px;
                padding: 12px 16px;
                color: #e0e0e0;
                line-height: 2;
            ">
                <div style="color: #00d4ff; letter-spacing: 1px; margin-bottom: 4px;">PIREP SEVERITY</div>
                <div><span style="color:#ff0000">●</span> Severe Turbulence / Icing</div>
                <div><span style="color:#ff6b00">●</span> Moderate Turbulence</div>
                <div><span style="color:#00aaff">●</span> Moderate Icing</div>
                <div><span style="color:#ffff00">●</span> Light Turbulence</div>
                <div><span style="color:#00ff88">●</span> No Significant WX</div>
                <div style="color: #00d4ff; letter-spacing: 1px; margin-top: 8px; margin-bottom: 4px;">SIGMET / AIRMET</div>
                <div><span style="color:#ff0000">■</span> Convective</div>
                <div><span style="color:#00aaff">■</span> Icing</div>
                <div><span style="color:#ff6b00">■</span> Other</div>
            </div>
            <style>
                #legend-toggle:not(:checked) ~ div { display: none; }
                #legend-toggle:checked + label { border-radius: 4px 4px 0 0; }
                #legend-toggle:not(:checked) + label { 
                    border-radius: 4px; 
                    border: 1px solid #0f3460;
                }
                #legend-toggle:checked + label::after { content: " ▲"; }
                #legend-toggle:not(:checked) + label::after { content: " ▼"; }
                #legend-toggle + label { display: block; }
            </style>
        </div>
        """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m._repr_html_()

from app.sigmets import get_route_sigmets

@main.route("/api/sigmets")
def sigmets():
    """
    GET /api/sigmets?origin=KORD&destination=KDEN
    Returns SIGMETs and AIRMETs intersecting the route corridor.
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

    try:
        results = get_route_sigmets(origin_coords, destination_coords)
        return jsonify({
            "origin": origin,
            "destination": destination,
            "count": len(results),
            "sigmets": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500