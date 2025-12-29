import csv
from io import StringIO, BytesIO
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash

from config import Settings
from db import make_engine, make_session_factory, Base
from models import Route, Sample
from services.waze_service import fetch_waze_route_geometry

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
            routes = db.query(Route).order_by(Route.id.desc()).all()
            default_route = routes[0] if routes else None

            last_by_route = {}
            if routes:
                for r in routes:
                    last_waze = db.query(Sample).filter(Sample.route_id == r.id, Sample.provider == "waze").order_by(Sample.ts_utc.desc()).first()
                    last_by_route[r.id] = {"waze": last_waze}

        return render_template("home.html", routes=routes, default_route=default_route, last_by_route=last_by_route)

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if request.method == "POST":
            try:
                name = (request.form.get("name") or "").strip()
                enabled = (request.form.get("enabled") == "on")

                start_lat = parse_float("start_lat", request.form["start_lat"])
                start_lng = parse_float("start_lng", request.form["start_lng"])
                end_lat = parse_float("end_lat", request.form["end_lat"])
                end_lng = parse_float("end_lng", request.form["end_lng"])
                waze_region = (request.form.get("waze_region") or s.WAZE_REGION).strip().upper()

                validate_lat_lng(start_lat, start_lng)
                validate_lat_lng(end_lat, end_lng)

                if not name:
                    name = f"{start_lat},{start_lng} -> {end_lat},{end_lng}"

                with Session() as db:
                    db.add(Route(
                        name=name[:64],
                        enabled=enabled,
                        start_lat=start_lat,
                        start_lng=start_lng,
                        end_lat=end_lat,
                        end_lng=end_lng,
                        waze_region=waze_region or "IL",
                    ))
                    db.commit()

                flash("Route added.", "ok")
                return redirect(url_for("setup"))
            except Exception as e:
                flash(str(e), "err")

        with Session() as db:
            routes = db.query(Route).order_by(Route.id.desc()).all()
        return render_template("setup.html", routes=routes)

    @app.post("/routes/<int:route_id>/toggle")
    def toggle_route(route_id: int):
        with Session() as db:
            r = db.query(Route).filter(Route.id == route_id).first()
            if not r:
                flash("Route not found", "err")
                return redirect(url_for("setup"))
            r.enabled = not r.enabled
            db.commit()
        return redirect(url_for("setup"))

    @app.post("/routes/<int:route_id>/delete")
    def delete_route(route_id: int):
        with Session() as db:
            r = db.query(Route).filter(Route.id == route_id).first()
            if not r:
                flash("Route not found", "err")
                return redirect(url_for("setup"))
            db.delete(r)
            db.commit()
        return redirect(url_for("setup"))

    @app.get("/status")
    def status():
        return render_template("status.html")

    @app.get("/api/routes")
    def api_routes():
        with Session() as db:
            routes = db.query(Route).order_by(Route.id.desc()).all()
        return jsonify([{
            "id": r.id,
            "name": r.name,
            "enabled": r.enabled,
            "start": [r.start_lat, r.start_lng],
            "end": [r.end_lat, r.end_lng],
            "waze_region": r.waze_region,
        } for r in routes])

    @app.get("/api/routes/<int:route_id>/path")
    def api_route_path(route_id: int):
        with Session() as db:
            r = db.query(Route).filter(Route.id == route_id).first()
            if not r:
                return jsonify({"error": "Route not found"}), 404

        try:
            points = fetch_waze_route_geometry(
                r.start_lat,
                r.start_lng,
                r.end_lat,
                r.end_lng,
                r.waze_region,
            )
        except Exception as exc:
            points = [[r.start_lat, r.start_lng], [r.end_lat, r.end_lng]]
            return jsonify({"points": points, "warning": str(exc)}), 200

        return jsonify({"points": points})

    @app.get("/api/samples")
    def api_samples():
        hours = int(request.args.get("hours", "168"))
        provider = request.args.get("provider")
        route_id = request.args.get("route_id")

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        with Session() as db:
            q = db.query(Sample).filter(Sample.ts_utc >= since)

            if provider == "waze":
                q = q.filter(Sample.provider == provider)

            if route_id:
                try:
                    rid = int(route_id)
                    q = q.filter(Sample.route_id == rid)
                except Exception:
                    pass

            items = q.order_by(Sample.ts_utc.asc()).all()

        def to_item(x: Sample):
            return {
                "ts": x.ts_utc.isoformat(),
                "route_id": x.route_id,
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
        provider = request.args.get("provider")
        route_id = request.args.get("route_id")

        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        with Session() as db:
            q = db.query(Sample).filter(Sample.ts_utc >= since)

            if provider == "waze":
                q = q.filter(Sample.provider == provider)

            if route_id:
                try:
                    rid = int(route_id)
                    q = q.filter(Sample.route_id == rid)
                except Exception:
                    pass

            items = q.order_by(Sample.ts_utc.asc()).all()

        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(["ts_utc", "route_id", "provider", "status", "duration_sec", "distance_m", "error"])
        for srow in items:
            w.writerow([srow.ts_utc.isoformat(), srow.route_id, srow.provider, srow.status, srow.duration_sec, srow.distance_m, srow.error])

        data = buf.getvalue().encode("utf-8")
        bio = BytesIO(data)
        bio.seek(0)
        filename = f"samples_last_{hours}h.csv"
        return send_file(bio, mimetype="text/csv", as_attachment=True, download_name=filename)

    return app

app = create_app()
