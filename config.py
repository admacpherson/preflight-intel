import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # URL References
    AVIATIONWEATHER_BASE_URL = "https://aviationweather.gov/api/data"
    SQLALCHEMY_DATABASE_URI = "sqlite:///data/db.sqlite3"

    # Filepath References
    DB_PATH = os.path.join(BASE_DIR, "data", "db.sqlite3")

    # Project Settings
    CORRIDOR_WIDTH_NM = 50          # Nautical miles each side of route
    POLL_INTERVAL_SECONDS = 300     # How often to poll ATIS/refresh dashboard (5 min)
    PIREP_ALTITUDE_LEVEL = 0  # 0 = all altitudes
    SH_DISTANCE = 500
    MD_DISTANCE = 1500
    PIREP_LOOKBACK_HOURS_SHORT = 2  # How far back to fetch PIREPs in hours (routes < 500nm / SH_DISTANCE)
    PIREP_LOOKBACK_HOURS_MED = 4    # How far back to fetch PIREPs in hours (routes < 1500nm / MD_DISTANCE)
    PIREP_LOOKBACK_HOURS_LONG = 6   # How far back to fetch PIREPs in hours (routes > 1500nm / MD_DISTANCE)
