Route Tracker (Waze + OSRM)

A small Flask app that runs all day, collects ETA and distance between two coordinates every 30 minutes, stores results in Postgres, and shows dashboards with charts and a map.
Providers

    Waze: Traffic-aware routing via WazeRouteCalculator.

    OSRM: Baseline routing (typically no live traffic) via a self-hosted OSRM HTTP server.

Core Pages

    /: Home dashboard (status, quick chart, map).

    /setup: Configure origin and destination coordinates.

    /status: Charts, recent samples table, and download link.

    /download: CSV export.

What You Get

    Persistent Storage: Postgres volume for long-term data.

    Always-on Collector: Separate container to avoid duplicated jobs if the web service scales.

    Visualization: Chart.js graphs and Leaflet map (OpenStreetMap tiles).

    Export: CSV download with optional provider filtering.

Requirements

    Docker Engine + Docker Compose plugin.

    Internet access (to download Python packages and OSM extracts).

Project Layout
Plaintext

route-tracker/
├── app.py
├── collector.py
├── config.py
├── db.py
├── models.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── services/
│   ├── osrm_service.py
│   └── waze_service.py
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── setup.html
│   └── status.html
├── static/
│   ├── app.js
│   └── styles.css
├── osrm-data/
│   └── README.md
└── scripts/
    └── download_osm_israel.sh

Quick Start
1. Create the Environment File
Bash

cp .env.example .env

Edit .env if you want to customize settings.
2. Download OSM Extract for OSRM

This example uses the Israel and Palestine extract from Geofabrik.
Bash

bash scripts/download_osm_israel.sh

This downloads osrm-data/israel-and-palestine-latest.osm.pbf.
3. Preprocess OSRM Data (One-time)

OSRM requires preprocessing to create .osrm.* files.
Bash

docker compose up osrm-prep

If successful, your osrm-data/ folder will contain several generated .osrm files.
4. Start the Full Stack
Bash

docker compose up --build

Services started:

    db: Postgres database.

    osrm: Routing server.

    web: Flask dashboard.

    collector: Poller running every 30 minutes.

5. Configure Your Route

    Open http://localhost:8000/setup

    Enter start_lat, start_lng, end_lat, end_lng, and waze_region (e.g., IL).

    Check http://localhost:8000/ for the dashboard or /status for charts.

Configuration

Environment variables (see .env.example):
Variable	Description
DATABASE_URL	e.g., postgresql+psycopg://user:pass@db:5432/db
FLASK_SECRET_KEY	Change this for production.
POLL_MINUTES	Default: 30. Collector aligns to the next 30-min boundary (UTC).
WAZE_REGION	Default: IL.
OSRM_URL	Default: http://osrm:5000.
Endpoints
UI

    GET /: Home dashboard (status, quick chart, map).

    GET /setup, POST /setup: Configure route coordinates.

    GET /status: Historical samples and filters.

API

    GET /api/config: Returns current route config.

    GET /api/samples?hours=168&provider=waze: Returns samples within N hours.

    GET /download?hours=168&provider=osrm: Downloads CSV export.

Data Model

The database consists of two tables:

    route_config: Stores the latest origin and destination coordinates.

    samples: Stores time-series data including timestamp, provider, status, duration_sec, and distance_m.

Common Operations
View Logs
Bash

docker compose logs -f web
docker compose logs -f collector
docker compose logs -f osrm

Reset Everything

To delete the database and all processed OSRM files:
Bash

docker compose down -v
rm -f osrm-data/*.osrm*

Troubleshooting

    OSRM prep fails: Ensure the .osm.pbf file exists in osrm-data/.

    Out of Memory: OSRM preprocessing is RAM-intensive. Use a smaller map extract if needed.

    Blank Map: Ensure your browser can reach OpenStreetMap tile servers and check for CSP blocks.

Security & Deployment

    Do not expose directly to the internet without authentication.

    Add Auth: Implement a login for /setup and /download.

    Proxy: Use Nginx or Caddy for HTTPS.