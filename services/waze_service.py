import json
from typing import Any
import WazeRouteCalculator

def fetch_waze_eta(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    region: str,
) -> dict[str, Any]:
    origin = f"{start_lat}, {start_lng}"
    dest = f"{end_lat}, {end_lng}"

    route = WazeRouteCalculator.WazeRouteCalculator(origin, dest, region)
    minutes, km = route.calc_route_info()

    duration_sec = int(round(float(minutes) * 60))
    distance_m = int(round(float(km) * 1000))

    return {
        "provider": "waze",
        "duration_sec": duration_sec,
        "distance_m": distance_m,
        "raw": json.dumps({"minutes": minutes, "km": km}, ensure_ascii=False),
    }
