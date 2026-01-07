Route Tracker (Waze)

A small Flask app that runs all day, collects ETA and distance between two coordinates every 30 minutes, stores results in Postgres, and shows dashboards with charts and a map.
Provider

    Waze: Traffic-aware routing via WazeRouteCalculator.

Core Pages

    /: Home dashboard (status, quick chart, map).

    /setup: Configure origin and destination coordinates.

    /status: Charts, recent samples table, and download link.

    /download: CSV export.

What You Get

    Persistent Storage: Postgres volume for long-term data.

    Always-on Collector: Separate container to avoid duplicated jobs if the web service scales.

    Visualization: Chart.js graphs and Leaflet map (OpenStreetMap tiles).

    Export: CSV download.

Requirements

    Docker Engine + Docker Compose plugin.

    Internet access (to download Python packages).

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
│   └── waze_service.py
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── setup.html
│   └── status.html
├── static/
│   ├── app.js
│   └── styles.css

Quick Start
1. Create the Environment File
Bash

cp .env.example .env

Edit .env if you want to customize settings.
2. Start the Full Stack
Bash

docker compose up --build

Services started:

    db: Postgres database.

    web: Flask dashboard.

    collector: Poller running every 30 minutes.

3. Configure Your Route

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
Endpoints
UI

    GET /: Home dashboard (status, quick chart, map).

    GET /setup, POST /setup: Configure route coordinates.

    GET /status: Historical samples and filters.

API

    GET /api/config: Returns current route config.

    GET /api/samples?hours=168: Returns samples within N hours.

    GET /download?hours=168: Downloads CSV export.

Data Model

The database consists of two tables:

    route_config: Stores the latest origin and destination coordinates.

    samples: Stores time-series data including timestamp, provider, status, duration_sec, and distance_m.

Common Operations
View Logs
Bash

docker compose logs -f web
docker compose logs -f collector

Reset Everything

To delete the database:
Bash

docker compose down -v

Troubleshooting

    Blank Map: Ensure your browser can reach OpenStreetMap tile servers and check for CSP blocks.

Security & Deployment

    Do not expose directly to the internet without authentication.

    Add Auth: Implement a login for /setup and /download.

    Proxy: Use Nginx or Caddy for HTTPS.
