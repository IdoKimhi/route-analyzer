import json
from typing import Any
import requests

def fetch_osrm_eta(
    osrm_url: str,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
) -> dict[str, Any]:
    # OSRM expects lon,lat ordering
    coords = f"{start_lng},{start_lat};{end_lng},{end_lat}"
    url = f"{osrm_url}/route/v1/driving/{coords}"

    r = requests.get(url, params={"overview": "false"}, timeout=10)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"OSRM bad response: {data.get('code')}")

    route = data["routes"][0]
    return {
        "provider": "osrm",
        "duration_sec": int(route["duration"]),
        "distance_m": int(route["distance"]),
        "raw": json.dumps(data, ensure_ascii=False),
    }
