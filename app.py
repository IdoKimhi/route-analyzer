import csv
from io import StringIO, BytesIO
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash

from config import Settings
from db import make_engine, make_session_factory, Base
from models import RouteConfig, Sample

load_dotenv()

def parse_float(name: str, v: str) -> float:
    try:
        return float(v)
    except Exception:
        raise ValueError(f"Invalid {name}")

def validate_lat_lng(lat: float, lng: float):
    if not (-90.0 <= lat <= 90.0):
        raise ValueError("Latitude out of range")
    if not (-180.0 <= lng <= 180.0):
        raise ValueError("Longitude out of range")

def create_app() -> Flask:
    s = Settings()
    app = Flask(__name__)
    app.secret_key = s.SECRET_KEY

    engine = make_engine(s.DATABASE_URL)
    Session = make_session_factory(engine)
    Base.metadata.create_all(engine)

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/")
    def home():
        with Session() as db:
            cfg = db.query(RouteConfig).order_by(RouteConfig.id.desc()).first()
            last_waze = db.query(Sample).filter(Sample.provider == "waze").order_by(Sample.ts_utc.desc()).first()
            last_osrm = db.query(Sample).filter(Sample.provider == "osrm").order_by(Sample.ts_utc.desc()).first()
        return render_template("home.html", cfg=cfg, last_waze=last_waze, last_osrm=last_osrm)

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if request.method == "POST":
            try:
                start_lat = parse_float("start_lat", request.form["start_lat"])
                start_lng = parse_float("start_lng", request.form["start_lng"])
                end_lat = parse_float("end_lat", request.form["end_lat"])
                end_lng = parse_float("end_lng", request.form["end_lng"])
                waze_region = (request.form.get("waze_region") or s.WAZE_REGION).strip().upper()

                validate_lat_lng(start_lat, start_lng)
                validate_lat_lng(end_lat, end_lng)

                with Session() as db:
                    db.add(RouteConfig(
                        start_lat=start_lat,
                        start_lng=start_lng,
                        end_lat=end_lat,
                        end_lng=end_lng,
                        waze_region=waze_region or "IL",
                    ))
                    db.commit()

                flash("Saved route configuration.", "ok")
                return redirect(url_for("home"))
            except Exception as e:
                flash(str(e), "err")

        with Session() as db:
            cfg = db.query(RouteConfig).order_by(RouteConfig.id.desc()).first()
        return render_template("setup.html", cfg=cfg)

    @app.get("/status")
    def status():
        return render_template("status.html")

    @app.get("/api/config")
    def api_config():
        with Session() as db:
            cfg = db.query(RouteConfig).order_by(RouteConfig.id.desc()).first()
        if not cfg:
            return jsonify(None)
        return jsonify({
            "start": [cfg.start_lat, cfg.start_lng],
            "end": [cfg.end_lat, cfg.end_lng],
            "waze_region": cfg.waze_region,
        })

    @app.get("/api/samples")
    def api_samples():
        hours = int(request.args.get("hours", "168"))
        provider = request.args.get("provider")  # optional
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        with Session() as db:
            q = db.query(Sample).filter(Sample.ts_utc >= since)
            if provider in ("waze", "osrm"):
                q = q.filter(Sample.provider == provider)
            items = q.order_by(Sample.ts_utc.asc()).all()

        def to_item(x: Sample):
            return {
                "ts": x.ts_utc.isoformat(),
                "provider": x.provider,
                "status": x.status,
                "duration_min": (int(round(x.duration_sec / 60)) if x.duration_sec is not None else None),
                "distance_km": (round(x.distance_m / 1000, 2) if x.distance_m is not None else None),
                "error": x.error,
            }

        return jsonify([to_item(i) for i in items])

    @app.get("/download")
    def download():
        hours = int(request.args.get("hours", "168"))
        provider = request.args.get("provider")  # optional
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        with Session() as db:
            q = db.query(Sample).filter(Sample.ts_utc >= since)
            if provider in ("waze", "osrm"):
                q = q.filter(Sample.provider == provider)
            items = q.order_by(Sample.ts_utc.asc()).all()

        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(["ts_utc", "provider", "status", "duration_sec", "distance_m", "error"])
        for srow in items:
            w.writerow([srow.ts_utc.isoformat(), srow.provider, srow.status, srow.duration_sec, srow.distance_m, srow.error])

        data = buf.getvalue().encode("utf-8")
        bio = BytesIO(data)
        bio.seek(0)
        filename = f"samples_last_{hours}h.csv"
        return send_file(bio, mimetype="text/csv", as_attachment=True, download_name=filename)

    return app

app = create_app()
