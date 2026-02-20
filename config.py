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
    PIREP_LOOKBACK_HOURS = 2        # How far back to fetch PIREPs in hours
    PIREP_ALTITUDE_LEVEL = 0        # 0 = all altitudes