#!/usr/bin/env bash
set -euo pipefail

mkdir -p osrm-data

# Geofabrik "Israel and Palestine" extract page lists the latest PBF file.
# This script downloads the latest PBF to the name expected by docker-compose.
URL="https://download.geofabrik.de/asia/israel-and-palestine-latest.osm.pbf"

echo "Downloading: ${URL}"
curl -L "${URL}" -o "osrm-data/israel-and-palestine-latest.osm.pbf"

echo "Saved to: osrm-data/israel-and-palestine-latest.osm.pbf"
