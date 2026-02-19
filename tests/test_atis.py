import sqlite3
import pytest
from unittest.mock import patch
from app.atis import get_last_atis, save_atis, check_for_atis_change

# --- Fixtures ---

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Create a temporary SQLite database for each test."""
    db_path = str(tmp_path / "test.sqlite3")
    monkeypatch.setattr("app.atis.Config.DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE atis_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airport TEXT NOT NULL,
            identifier TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    return db_path


# --- Tests ---

def test_get_last_atis_empty(test_db):
    """Should return None when no ATIS has been stored yet."""
    result = get_last_atis("KORD")
    assert result is None


def test_save_and_retrieve_atis(test_db):
    """Should persist an ATIS record and retrieve it correctly."""
    atis = {
        "airport": "KORD",
        "identifier": "BRAVO",
        "raw_text": "KORD 191952Z 27015KT 10SM FEW045 BKN250 08/M04 A2992"
    }
    save_atis(atis)
    result = get_last_atis("KORD")
    assert result is not None
    assert result["airport"] == "KORD"
    assert result["identifier"] == "BRAVO"
    assert result["raw_text"] == atis["raw_text"]


def test_check_first_observation(test_db):
    """First call for an airport should save and report no change."""
    mock_atis = {
        "airport": "KORD",
        "identifier": "BRAVO",
        "raw_text": "KORD 191952Z 27015KT 10SM FEW045 BKN250 08/M04 A2992"
    }
    with patch("app.atis.fetch_atis", return_value=mock_atis):
        result = check_for_atis_change("KORD")
    assert result["changed"] == False
    assert result["reason"] == "First observation saved"


def test_check_detects_change(test_db):
    """Should detect when ATIS raw text changes between polls."""
    old_atis = {
        "airport": "KORD",
        "identifier": "BRAVO",
        "raw_text": "KORD 191952Z 27015KT 10SM FEW045 BKN250 08/M04 A2992"
    }
    new_atis = {
        "airport": "KORD",
        "identifier": "CHARLIE",
        "raw_text": "KORD 192052Z 28018KT 10SM SCT040 BKN200 07/M05 A2995"
    }
    save_atis(old_atis)
    with patch("app.atis.fetch_atis", return_value=new_atis):
        result = check_for_atis_change("KORD")
    assert result["changed"] == True
    assert result["previous"] == old_atis["raw_text"]
    assert result["current"] == new_atis["raw_text"]


def test_check_no_change(test_db):
    """Should report no change when ATIS is identical to last stored."""
    atis = {
        "airport": "KORD",
        "identifier": "BRAVO",
        "raw_text": "KORD 191952Z 27015KT 10SM FEW045 BKN250 08/M04 A2992"
    }
    save_atis(atis)
    with patch("app.atis.fetch_atis", return_value=atis):
        result = check_for_atis_change("KORD")
    assert result["changed"] == False
    assert result["reason"] == "No change detected"


def test_check_atis_unavailable(test_db):
    """Should handle gracefully when API returns no ATIS."""
    with patch("app.atis.fetch_atis", return_value=None):
        result = check_for_atis_change("KORD")
    assert result["changed"] == False
    assert result["reason"] == "No ATIS available"