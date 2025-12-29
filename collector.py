import time
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

from config import Settings
from db import make_engine, make_session_factory, Base
from models import RouteConfig, Sample
from services.waze_service import fetch_waze_eta
from services.osrm_service import fetch_osrm_eta

load_dotenv()

def seconds_until_next_slot(slot_minutes: int) -> int:
    if slot_minutes <= 0:
        return 60

    now = datetime.now(timezone.utc).replace(microsecond=0)
    minute = now.minute
    next_minute = ((minute // slot_minutes) + 1) * slot_minutes

    base = now.replace(second=0)
    if next_minute >= 60:
        next_time = (base + timedelta(hours=1)).replace(minute=0)
    else:
        next_time = base.replace(minute=next_minute)

    return max(1, int((next_time - now).total_seconds()))

def main():
    s = Settings()
    engine = make_engine(s.DATABASE_URL)
    Session = make_session_factory(engine)
    Base.metadata.create_all(engine)

    while True:
        with Session() as db:
            cfg = db.query(RouteConfig).order_by(RouteConfig.id.desc()).first()
            if not cfg:
                print("[collector] No route configured yet. Sleeping 60s.")
                time.sleep(60)
                continue

            # Waze
            try:
                w = fetch_waze_eta(cfg.start_lat, cfg.start_lng, cfg.end_lat, cfg.end_lng, cfg.waze_region)
                db.add(Sample(provider="waze", status="ok", duration_sec=w["duration_sec"], distance_m=w["distance_m"], raw_json=w["raw"]))
            except Exception as e:
                db.add(Sample(provider="waze", status="error", error=str(e)[:512]))
                print(f"[collector] Waze error: {e}")

            # OSRM
            try:
                o = fetch_osrm_eta(s.OSRM_URL, cfg.start_lat, cfg.start_lng, cfg.end_lat, cfg.end_lng)
                db.add(Sample(provider="osrm", status="ok", duration_sec=o["duration_sec"], distance_m=o["distance_m"], raw_json=o["raw"]))
            except Exception as e:
                db.add(Sample(provider="osrm", status="error", error=str(e)[:512]))
                print(f"[collector] OSRM error: {e}")

            db.commit()

        sleep_s = seconds_until_next_slot(s.POLL_MINUTES)
        print(f"[collector] Sleeping {sleep_s}s until next slot.")
        time.sleep(sleep_s)

if __name__ == "__main__":
    main()
