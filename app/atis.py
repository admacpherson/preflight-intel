import sqlite3
import requests
from config import Config

def fetch_atis(airport_icao: str) -> dict | None:
    """
    Fetch current ATIS for a given airport from AviationWeather.gov.
    Returns a dict with 'identifier' and 'raw_text', or None if unavailable.
    """
    url = f"{Config.AVIATIONWEATHER_BASE_URL}/metar"
    params = {
        "ids": airport_icao,
        "format": "json",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if not data:
        return None

    metar = data[0]
    return {
        "airport": airport_icao,
        "identifier": metar.get("metarType", "UNKNOWN"),
        "raw_text": metar.get("rawOb", ""),
    }


def get_last_atis(airport_icao: str) -> dict | None:
    """Retrieve the most recently stored ATIS for an airport from SQLite."""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT airport, identifier, raw_text, fetched_at
        FROM atis_log
        WHERE airport = ?
        ORDER BY fetched_at DESC
        LIMIT 1
    """, (airport_icao,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    return {"airport": row[0], "identifier": row[1], "raw_text": row[2], "fetched_at": row[3]}


def save_atis(atis: dict):
    """Persist a fresh ATIS record to SQLite."""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO atis_log (airport, identifier, raw_text)
        VALUES (?, ?, ?)
    """, (atis["airport"], atis["identifier"], atis["raw_text"]))
    conn.commit()
    conn.close()


def check_for_atis_change(airport_icao: str) -> dict:
    """
    Core function: fetch current ATIS, compare to last known, save if changed.
    Returns a dict describing what happened.
    """
    current = fetch_atis(airport_icao)
    if not current:
        return {"changed": False, "airport": airport_icao, "reason": "No ATIS available"}

    last = get_last_atis(airport_icao)

    if not last:
        save_atis(current)
        return {
            "changed": False,
            "airport": airport_icao,
            "reason": "First observation saved",
            "current": current["raw_text"]
        }

    if current["raw_text"] != last["raw_text"]:
        save_atis(current)
        return {
            "changed": True,
            "airport": airport_icao,
            "previous": last["raw_text"],
            "current": current["raw_text"],
        }

    return {
        "changed": False,
        "airport": airport_icao,
        "reason": "No change detected",
        "current": current["raw_text"]
    }