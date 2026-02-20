# preflight-intel
A tool for pilots to view weather conditions by pulling ATIS and PIREPs along a specified route.

---

## Features
**Route-Aware PIREP Feed**
Pilot weather reports (PIREPs) are fetched from AviationWeather.gov and filtered to a 50nm corridor around your route. Each report is plotted on the map with color-coded severity markers — red for severe turbulence or icing, orange for moderate turbulence, blue for moderate icing, yellow for light turbulence, and green for no significant weather.

**ATIS Change Detection**
ATIS is polled at your departure and destination airports and stored locally. When the information identifier changes (e.g. Bravo → Charlie), the dashboard flags exactly what changed so you don't have to manually re-check before departure.

**SIGMET / AIRMET Overlay**
Active SIGMETs and AIRMETs that intersect your route corridor are displayed both on the map as shaded polygons and in the data panel. Convective SIGMETs, icing, and turbulence advisories are color-coded for quick recognition.

**Auto-Refresh**
Once a route is loaded, all three data sources refresh automatically every 5 minutes so you can monitor conditions leading up to departure without manually reloading.

---

## Repository Structure
```
preflight-intel/
├── app/
│   ├── __init__.py        # App factory and database initialization
│   ├── airports.py        # Airport lookup from OurAirports database
│   ├── atis.py            # ATIS fetching and change detection
│   ├── corridor.py        # Route corridor geometry
│   ├── pireps.py          # PIREP fetching and corridor filtering
│   ├── routes.py          # Flask route handlers
│   └── sigmets.py         # SIGMET/AIRMET fetching and filtering
├── data/
│   └── db.sqlite3         # Local database (gitignored)
├── static/
│   ├── css/
│   │   └── dashboard.css  # Dashboard styles
│   └── js/
│       └── dashboard.js   # Dashboard logic and API calls
├── templates/
│   └── index.html         # Main dashboard template
├── tests/
│   ├── conftest.py        # Pytest path configuration
│   ├── test_atis.py       # ATIS unit tests
│   └── test_pireps.py     # PIREP and corridor unit tests
├── .gitignore
├── config.py              # App configuration
├── requirements.txt
├── pytest.ini             # Pytest path and test configuration
└── run.py                 # Entry point
```
---

## Usage

1. Enter your departure airport ICAO code in the **origin** field (e.g. `KORD`)
2. Enter your destination ICAO code in the **destination** field (e.g. `KDEN`)
3. Click **LOAD ROUTE**
4. The map will display your route with PIREP markers and SIGMET polygons
5. Use the **PIREPs**, **ATIS**, and **SIGMETs** tabs in the right panel to review conditions
6. Data refreshes automatically every 5 minutes (or as configured)

---

## Configuration

All configurable values in `config.py`. You can modify these to use the tool to your liking.

| Setting                 | Default | Description                                                 |
|-------------------------|---------|-------------------------------------------------------------|
| `CORRIDOR_WIDTH_NM`     | `50`    | Width of the route corridor in nautical miles (each side)   |
| `PIREP_LOOKBACK_HOURS`  | `2`     | How far back to fetch PIREPs in hours                       |
| `POLL_INTERVAL_SECONDS` | `300`   | How often the dashboard auto-refreshes (seconds)            |
| `PIREP_ALTITUDE_LEVEL`  | `0`     | Altitudes at which to get PIREPS (0 includes all altitudes) |

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/admacpherson/preflight-intel.git
cd preflight-intel
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the app**
```bash
python run.py
```

**5. Open your browser**
```
http://127.0.0.1:5000
```

On first run, the airport database will download automatically from OurAirports (~12.5MB). This only happens once.

---

## Data Sources

| Source              | Data                             | URL                             |
|---------------------|----------------------------------|---------------------------------|
| AviationWeather.gov | PIREPs, ATIS, SIGMETs, AIRMETs   | https://aviationweather.gov/api |
| OurAirports         | Airport coordinates and metadata | https://ourairports.com         |
All data is fetched live from free, public APIs, except for the [OurAirports](https://ourairports.com) database for airport coordinate lookups. It will download automatically on first run, or you can download it manually:
```bash
curl -o data/airports.csv \
  https://davidmegginson.github.io/ourairports-data/airports.csv
```
No API keys are required at any point.

---

# Disclaimer

Preflight Intel is intended as a supplementary situational awareness tool only. It is **not** a certified weather briefing service and should **not** be used as a substitute for an official FAA weather briefing. Always obtain a full weather briefing from an approved source (1800wxbrief.com, ForeFlight, etc.) before flight.