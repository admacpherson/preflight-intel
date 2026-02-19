import csv
import io
import os
import requests

AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
AIRPORTS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "airports.csv")

_cache = {}

def download_airports_csv():
    """Download airports.csv from OurAirports if not already present."""
    if os.path.exists(AIRPORTS_CSV):
        return
    print("Downloading airports database...")
    os.makedirs(os.path.dirname(AIRPORTS_CSV), exist_ok=True)
    response = requests.get(AIRPORTS_URL, timeout=30)
    response.raise_for_status()
    with open(AIRPORTS_CSV, "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Airports database downloaded successfully.")


def load_airports():
    """Load airport data from CSV into memory cache."""
    if _cache:
        return _cache
    download_airports_csv()
    with open(AIRPORTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            icao = row.get("ident", "").strip().upper()
            try:
                lat = float(row["latitude_deg"])
                lon = float(row["longitude_deg"])
                _cache[icao] = {
                    "icao": icao,
                    "name": row.get("name", ""),
                    "latitude": lat,
                    "longitude": lon,
                }
            except (ValueError, KeyError):
                continue
    return _cache


def get_airport(icao: str) -> dict | None:
    """Look up a single airport by ICAO code."""
    airports = load_airports()
    return airports.get(icao.strip().upper())


def get_coords(icao: str) -> tuple | None:
    """Return (lat, lon) tuple for an airport, or None if not found."""
    airport = get_airport(icao)
    if airport:
        return (airport["latitude"], airport["longitude"])
    return None