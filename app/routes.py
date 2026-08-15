from __future__ import annotations

import csv
import io

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from . import analytics
from .db import connect
from .importer import import_uploads

pages = Blueprint("pages", __name__)
api = Blueprint("api", __name__)


@pages.get("/")
def index():
    return render_template("index.html")


@api.get("/health")
def health():
    with connect(_database()) as connection:
        connection.execute("SELECT 1").fetchone()
    return jsonify(status="ok")


@api.get("/summary")
def get_summary():
    return jsonify(
        analytics.summary(_database(), request.args.get("start"), request.args.get("end"))
    )


@api.get("/top")
def get_top():
    try:
        result = analytics.top_entities(
            _database(),
            request.args.get("entity", "artists"),
            request.args.get("metric", "time"),
            request.args.get("limit", type=int, default=25),
            request.args.get("start"),
            request.args.get("end"),
        )
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(result)


@api.get("/timeline")
def get_timeline():
    try:
        result = analytics.timeline(
            _database(), request.args.get("start"), request.args.get("end"),
            request.args.get("granularity", "auto")
        )
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(result)


@api.get("/calendar")
def get_calendar():
    return jsonify(
        analytics.calendar(_database(), request.args.get("start"), request.args.get("end"))
    )


@api.get("/search")
def get_search():
    query = request.args.get("q", "").strip()
    empty = {"artists": [], "tracks": [], "albums": []}
    return jsonify(analytics.search(_database(), query) if query else empty)


@api.get("/entity/<entity>")
def get_entity(entity: str):
    artist = request.args.get("artist", "").strip()
    if not artist:
        return jsonify(error="artist is required"), 400
    try:
        result = analytics.entity_details(_database(), entity, artist, request.args.get("name"))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    return jsonify(result)


@api.get("/diagnostics")
def get_diagnostics():
    return jsonify(analytics.diagnostics(_database()))


@api.get("/years")
def get_years():
    return jsonify(analytics.years(_database()))


@api.post("/import")
def import_data():
    files = request.files.getlist("files")
    if not files or not any(item.filename for item in files):
        return jsonify(error="Choose at least one Spotify ZIP or JSON file."), 400
    report = import_uploads(_database(), files)
    current_app.logger.info(
        "Import completed: accepted=%s duplicates=%s ignored=%s",
        report.accepted, report.duplicates, report.ignored
    )
    status = 200 if report.accepted or report.duplicates else 422
    return jsonify(report.to_dict()), status


@api.delete("/data")
def delete_data():
    confirmation = request.get_json(silent=True) or {}
    if confirmation.get("confirm") != "DELETE":
        return jsonify(error='Send {"confirm":"DELETE"} to remove local history.'), 400
    with connect(_database()) as connection:
        deleted = connection.execute("SELECT COUNT(*) FROM listening_events").fetchone()[0]
        connection.execute("DELETE FROM listening_events")
        connection.execute("DELETE FROM import_runs")
        connection.commit()
        connection.execute("VACUUM")
    current_app.logger.warning("Local dataset deleted: %s events", deleted)
    return jsonify(deleted=deleted, status="ok")


@api.get("/export.csv")
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    fields = [
        "timestamp", "artist_name", "track_name", "album_name", "ms_played", "platform",
        "country", "shuffle", "skipped", "offline", "spotify_track_uri", "source_file"
    ]
    writer.writerow(fields)
    with connect(_database()) as connection:
        cursor = connection.execute(
            f"SELECT {', '.join(fields)} FROM listening_events ORDER BY timestamp"
        )
        writer.writerows(cursor)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=spotify_normalized_history.csv"},
    )


def _database() -> str:
    return current_app.config["DATABASE"]
