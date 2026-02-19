import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    AVIATIONWEATHER_BASE_URL = "https://aviationweather.gov/api/data"
    POLL_INTERVAL_SECONDS = 300       # How often to poll ATIS (5 min)
    CORRIDOR_WIDTH_NM = 50            # Nautical miles each side of route
    SQLALCHEMY_DATABASE_URI = "sqlite:///data/db.sqlite3"
    ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")