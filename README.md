# preflight-intel
A tool for pilots to view weather conditions by pulling ATIS and PIREPs along a specified route

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

## Setup

### Airport Database
This project uses the [OurAirports](https://ourairports.com) database for airport coordinate lookups. It will download automatically on first run, or you can download it manually:
```bash
curl -o data/airports.csv \
  https://davidmegginson.github.io/ourairports-data/airports.csv
```