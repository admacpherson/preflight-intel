import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # URL references
    AVIATIONWEATHER_BASE_URL = "https://aviationweather.gov/api/data"
    SQLALCHEMY_DATABASE_URI = "sqlite:///data/db.sqlite3"

    # Filepath references
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    DB_PATH = os.path.join(BASE_DIR, "data", "db.sqlite3")

    # Project settings
    CORRIDOR_WIDTH_NM = 50  # Nautical miles each side of route

    # ATIS Settings
    POLL_INTERVAL_SECONDS = 300       # How often to poll ATIS (5 min)

    # Pirep settings
    PIREP_LOOKBACK_HOURS = 2
    PIREP_ALTITUDE_LEVEL = 0  # 0 = all altitudes

    # Other
    ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")