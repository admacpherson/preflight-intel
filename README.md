# preflight-intel
A tool for pilots to view weather conditions by pulling ATIS and PIREPs along a specified route

## Repository Structure
```
preflight-intel/
├── app/
│   ├── __init__.py
│   ├── routes.py          # Flask route handlers
│   ├── pireps.py          # PIREP fetching + filtering logic
│   ├── atis.py            # ATIS polling + diff logic
│   ├── sigmets.py         # SIGMET/AIRMET fetching + filtering
│   ├── corridor.py        # Route corridor geometry (shapely)
│   └── alerts.py          # Email/SMS alert dispatching
├── static/
│   ├── css/
│   └── js/
├── templates/
│   └── index.html         # Main dashboard
├── data/
│   └── db.sqlite3         # SQLite database (gitignored)
├── tests/
│   ├── test_pireps.py
│   ├── test_atis.py
│   └── test_corridor.py
├── .env                   # API keys, secrets (gitignored)
├── .gitignore
├── requirements.txt
├── config.py              # App configuration
└── run.py                 # Entry point
```