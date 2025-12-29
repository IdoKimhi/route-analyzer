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

    route = WazeRouteCalculator.WazeRouteCalculator(
        origin,
        dest,
        region,
        avoid_toll_roads=True,
    )
    minutes, km = route.calc_route_info()

    duration_sec = int(round(float(minutes) * 60))
    distance_m = int(round(float(km) * 1000))

    return {
        "provider": "waze",
        "duration_sec": duration_sec,
        "distance_m": distance_m,
        "raw": json.dumps({"minutes": minutes, "km": km}, ensure_ascii=False),
    }


def fetch_waze_route_geometry(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    region: str,
) -> list[list[float]]:
    origin = f"{start_lat}, {start_lng}"
    dest = f"{end_lat}, {end_lng}"

    route = WazeRouteCalculator.WazeRouteCalculator(
        origin,
        dest,
        region,
        avoid_toll_roads=True,
    )
    response = route.get_route(1)
    results = response.get("results") or response.get("result") or []

    points: list[list[float]] = []

    def add_point(lat: float, lng: float) -> None:
        if not points or points[-1] != [lat, lng]:
            points.append([lat, lng])

    for segment in results:
        path = segment.get("path")
        if isinstance(path, list):
            for item in path:
                if isinstance(item, dict) and "x" in item and "y" in item:
                    add_point(float(item["y"]), float(item["x"]))
        elif isinstance(path, dict) and "x" in path and "y" in path:
            add_point(float(path["y"]), float(path["x"]))

    if not points:
        points = [[start_lat, start_lng], [end_lat, end_lng]]

    return points
