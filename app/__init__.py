from flask import Flask
from config import Config
import sqlite3
import os

# Set up SQLite DB
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atis_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airport TEXT NOT NULL,
            identifier TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Create Flask app
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db()

    from app.routes import main
    app.register_blueprint(main)

    return app

