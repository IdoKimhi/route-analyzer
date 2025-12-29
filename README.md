# Route Tracker (Waze + OSRM)

A small Flask app that runs all day, collects ETA and distance between two coordinates every 30 minutes, stores results in Postgres, and shows dashboards with charts and a map.

Providers:
- Waze (traffic-aware) via `WazeRouteCalculator`
- OSRM (baseline routing, typically no live traffic) via a self-hosted OSRM HTTP server

Core pages:
- `/` Home dashboard (status, quick chart, map)
- `/setup` Configure origin and destination coordinates
- `/status` Charts, recent samples table, download link
- `/download` CSV export

## What you get

- Persistent storage (Postgres volume)
- Always-on collector (separate container) to avoid duplicated jobs if web scales
- Chart.js graphs and Leaflet map (OpenStreetMap tiles)
- CSV download with optional provider filter

## Requirements

- Docker Engine + Docker Compose plugin
- Internet access to download Python packages and OSM extract

## Project layout

```text
route-tracker/
  app.py
  collector.py
  config.py
  db.py
  models.py
  requirements.txt
  Dockerfile
  docker-compose.yml
  .env.example
  services/
    osrm_service.py
    waze_service.py
  templates/
    base.html
    home.html
    setup.html
    status.html
  static/
    app.js
    styles.css
  osrm-data/
    README.md
  scripts/
    download_osm_israel.sh

Quick start
1) Create the env file

cp .env.example .env

Edit .env if you want different settings.
2) Download OSM extract for OSRM

This example is for Israel and Palestine (Geofabrik extract).

bash scripts/download_osm_israel.sh

This downloads:

osrm-data/israel-and-palestine-latest.osm.pbf

3) Preprocess OSRM data (one-time)

OSRM needs preprocessing to create .osrm.* files. This runs once and writes output into ./osrm-data.

docker compose up osrm-prep

If the preprocessing succeeds, you will see generated files like:

osrm-data/israel-and-palestine-latest.osrm
osrm-data/israel-and-palestine-latest.osrm.*   (many files)

4) Start the full stack

docker compose up --build

Services started:

    db (Postgres)

    osrm (routing server)

    web (Flask dashboards)

    collector (poller running every 30 minutes)

5) Configure your route

Open:

    http://localhost:8000/setup

Enter:

    start_lat, start_lng

    end_lat, end_lng

    waze_region (example: IL)

Then check:

    http://localhost:8000/
    (Home)

    http://localhost:8000/status
    (Charts and table)

Configuration

Environment variables (see .env.example):

    DATABASE_URL

        Example:

            postgresql+psycopg://route_tracker:route_tracker@db:5432/route_tracker

    FLASK_SECRET_KEY

        Change this in real deployments

    POLL_MINUTES

        Default: 30

        Collector aligns to the next 30-minute boundary (UTC), not a fixed sleep loop

    WAZE_REGION

        Default: IL

    OSRM_URL

        In Compose, default is internal:

            http://osrm:5000

Endpoints
UI

    GET /

        Home dashboard: provider status, quick chart, map markers

    GET /setup, POST /setup

        Configure route coordinates (saved to DB)

    GET /status

        Filters and chart for historical samples

API

    GET /api/config

        Returns current route config (or null)

    GET /api/samples?hours=168&provider=waze|osrm

        Returns samples within the last N hours

        Provider filter is optional

    GET /download?hours=168&provider=waze|osrm

        Downloads CSV

Health

    GET /health

        Simple health check from the web container

Data model

Two tables:

    route_config

        Stores the latest configured origin and destination coordinates

    samples

        Stores time series data:

            timestamp (UTC)

            provider (waze or osrm)

            status (ok or error)

            duration_sec, distance_m

            error string and optional raw JSON

Notes and limitations
Waze

    Waze results can fail intermittently (rate limits, service changes, blocks).

    The app records errors as samples so you can see provider availability over time.

OSRM

    OSRM provides a baseline ETA based on its routing profile and data, usually not live traffic.

    OSRM preprocessing can take time depending on region size and machine resources.

    If you pick a larger region, memory and disk usage increase significantly.

Common operations
View logs

docker compose logs -f web
docker compose logs -f collector
docker compose logs -f osrm

Reset everything (including DB and OSRM processed files)

This deletes the Postgres volume and OSRM generated files.

docker compose down -v
rm -f osrm-data/*.osrm*

If you want to also delete the downloaded .pbf:

rm -f osrm-data/*.pbf

Changing the OSRM region

    Download a different .osm.pbf into osrm-data/

    Update docker-compose.yml to reference the new filename in both osrm-prep and osrm

    Remove old .osrm.* files

    Re-run:

docker compose up osrm-prep
docker compose up --build

Troubleshooting
OSRM prep fails with "Missing ... .osm.pbf"

    Ensure osrm-data/israel-and-palestine-latest.osm.pbf exists

    Re-run the download script

OSRM prep is slow or runs out of memory

    Use a smaller extract (city or smaller region)

    Increase Docker memory limits if using Docker Desktop

    Run on a machine with more RAM

Collector shows "No route configured yet"

    Visit /setup and save coordinates

    Then wait until the next polling slot or restart collector:

docker compose restart collector

The map is blank

    Confirm your browser can load OpenStreetMap tile URLs

    Check browser console for blocked mixed content or CSP issues

Security and deployment notes

    Do not expose this directly to the internet without auth.

    If deploying publicly, add:

        authentication for /setup and /download

        rate limiting

        HTTPS (reverse proxy like Nginx or Caddy)

    Store secrets in your deployment environment, not in git.

License and compliance note

    Verify the license of WazeRouteCalculator and OSRM components matches your intended usage and distribution.

Next improvements

    Support multiple saved routes (not just the latest)

    Add retention policy (delete samples older than N days)

    Add alerts (ETA threshold or provider down)

    Add a proper /api/export that can export JSON and CSV zipped

    Add admin auth for /setup and /download

::contentReference[oaicite:0]{index=0}
