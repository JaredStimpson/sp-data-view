from __future__ import annotations

import json
from datetime import datetime, timezone

from .db import connect


def _where(start: str | None, end: str | None, alias: str = "") -> tuple[str, list[str]]:
    prefix = f"{alias}." if alias else ""
    clauses: list[str] = []
    parameters: list[str] = []
    if start:
        clauses.append(f"{prefix}timestamp >= ?")
        parameters.append(_date_boundary(start, end=False))
    if end:
        clauses.append(f"{prefix}timestamp < ?")
        parameters.append(_date_boundary(end, end=True))
    return (" WHERE " + " AND ".join(clauses) if clauses else ""), parameters


def _date_boundary(value: str, end: bool) -> str:
    parsed = datetime.fromisoformat(value[:10]).replace(tzinfo=timezone.utc)
    if end:
        from datetime import timedelta

        parsed += timedelta(days=1)
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def summary(database: str, start: str | None, end: str | None) -> dict:
    where, params = _where(start, end)
    with connect(database) as connection:
        row = connection.execute(
            f"""SELECT COUNT(*) AS plays,
                       COALESCE(SUM(ms_played), 0) AS total_ms,
                       COUNT(DISTINCT artist_name) AS unique_artists,
                       COUNT(DISTINCT artist_name || char(31) || track_name) AS unique_tracks,
                       COUNT(DISTINCT CASE WHEN album_name IS NOT NULL THEN
                           artist_name || char(31) || album_name END) AS unique_albums,
                       MIN(timestamp) AS first_play,
                       MAX(timestamp) AS last_play,
                       COUNT(DISTINCT date(timestamp)) AS listening_days
                FROM listening_events{where}""",
            params,
        ).fetchone()
        result = dict(row)
        result["hours"] = round(result["total_ms"] / 3_600_000, 1)
        result["average_minutes_per_listening_day"] = round(
            result["total_ms"] / 60_000 / max(result["listening_days"], 1), 1
        )
        for entity in ("artists", "tracks", "albums"):
            rows = top_entities(database, entity, "time", 1, start, end)
            result[f"top_{entity[:-1]}"] = rows[0] if rows else None
        return result


def top_entities(database: str, entity: str, metric: str, limit: int,
                 start: str | None, end: str | None) -> list[dict]:
    configurations = {
        "artists": ("artist_name", "artist_name IS NOT NULL"),
        "tracks": (
            "artist_name, track_name",
            "artist_name IS NOT NULL AND track_name IS NOT NULL",
        ),
        "albums": (
            "artist_name, album_name",
            "album_name IS NOT NULL AND album_name != ''",
        ),
    }
    if entity not in configurations:
        raise ValueError("entity must be artists, tracks, or albums")
    if metric not in {"time", "plays", "days"}:
        raise ValueError("metric must be time, plays, or days")
    group_columns, required = configurations[entity]
    where, params = _where(start, end)
    where = f"{where} {'AND' if where else 'WHERE'} {required}"
    order = {
        "time": "total_ms DESC",
        "plays": "play_count DESC, total_ms DESC",
        "days": "unique_days DESC, total_ms DESC",
    }[metric]
    limit = min(max(int(limit), 1), 500)
    with connect(database) as connection:
        total = connection.execute(
            f"SELECT COALESCE(SUM(ms_played), 0) FROM listening_events{where}", params
        ).fetchone()[0]
        rows = connection.execute(
            f"""SELECT {group_columns}, SUM(ms_played) AS total_ms,
                       COUNT(*) AS play_count,
                       COUNT(DISTINCT date(timestamp)) AS unique_days,
                       MIN(timestamp) AS first_play, MAX(timestamp) AS last_play
                FROM listening_events{where}
                GROUP BY {group_columns}
                ORDER BY {order}
                LIMIT ?""",
            [*params, limit],
        ).fetchall()
    results = []
    for rank, row in enumerate(rows, 1):
        item = dict(row)
        item["rank"] = rank
        item["hours"] = round(item["total_ms"] / 3_600_000, 2)
        item["share"] = round(item["total_ms"] * 100 / total, 2) if total else 0
        results.append(item)
    return results


def timeline(database: str, start: str | None, end: str | None,
             granularity: str = "auto") -> list[dict]:
    if granularity == "auto":
        granularity = _choose_granularity(start, end)
    formats = {"day": "%Y-%m-%d", "month": "%Y-%m", "year": "%Y"}
    if granularity not in formats:
        raise ValueError("granularity must be auto, day, month, or year")
    where, params = _where(start, end)
    with connect(database) as connection:
        rows = connection.execute(
            f"""SELECT strftime('{formats[granularity]}', timestamp) AS period,
                       SUM(ms_played) AS total_ms, COUNT(*) AS plays,
                       COUNT(DISTINCT artist_name) AS artists
                FROM listening_events{where}
                GROUP BY period ORDER BY period""",
            params,
        ).fetchall()
    return [
        {**dict(row), "hours": round(row["total_ms"] / 3_600_000, 2),
         "granularity": granularity}
        for row in rows
    ]


def calendar(database: str, start: str | None, end: str | None) -> list[dict]:
    where, params = _where(start, end)
    with connect(database) as connection:
        rows = connection.execute(
            f"""SELECT date(timestamp) AS date, SUM(ms_played) AS total_ms,
                       COUNT(*) AS plays, COUNT(DISTINCT artist_name) AS artists
                FROM listening_events{where}
                GROUP BY date(timestamp) ORDER BY date(timestamp)""",
            params,
        ).fetchall()
    return [{**dict(row), "minutes": round(row["total_ms"] / 60_000, 1)} for row in rows]


def search(database: str, query: str, limit: int = 20) -> dict:
    escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    limit = min(max(limit, 1), 50)
    with connect(database) as connection:
        artists = connection.execute(
            """SELECT artist_name, SUM(ms_played) AS total_ms, COUNT(*) AS play_count
               FROM listening_events WHERE artist_name LIKE ? ESCAPE '\\'
               GROUP BY artist_name ORDER BY total_ms DESC LIMIT ?""",
            (pattern, limit),
        ).fetchall()
        tracks = connection.execute(
            """SELECT artist_name, track_name, album_name, SUM(ms_played) AS total_ms,
                      COUNT(*) AS play_count
               FROM listening_events WHERE track_name LIKE ? ESCAPE '\\'
               GROUP BY artist_name, track_name ORDER BY total_ms DESC LIMIT ?""",
            (pattern, limit),
        ).fetchall()
        albums = connection.execute(
            """SELECT artist_name, album_name, SUM(ms_played) AS total_ms,
                      COUNT(*) AS play_count
               FROM listening_events
               WHERE album_name IS NOT NULL AND album_name LIKE ? ESCAPE '\\'
               GROUP BY artist_name, album_name ORDER BY total_ms DESC LIMIT ?""",
            (pattern, limit),
        ).fetchall()
    return {
        "artists": [_result_with_hours(row) for row in artists],
        "tracks": [_result_with_hours(row) for row in tracks],
        "albums": [_result_with_hours(row) for row in albums],
    }


def entity_details(database: str, entity: str, artist: str,
                   name: str | None = None) -> dict:
    if entity == "artist":
        where = "artist_name = ? COLLATE NOCASE"
        params = [artist]
    elif entity == "track":
        where = "artist_name = ? COLLATE NOCASE AND track_name = ? COLLATE NOCASE"
        params = [artist, name or ""]
    elif entity == "album":
        where = "artist_name = ? COLLATE NOCASE AND album_name = ? COLLATE NOCASE"
        params = [artist, name or ""]
    else:
        raise ValueError("entity must be artist, track, or album")
    with connect(database) as connection:
        stats = connection.execute(
            f"""SELECT SUM(ms_played) AS total_ms, COUNT(*) AS play_count,
                       COUNT(DISTINCT date(timestamp)) AS unique_days,
                       COUNT(DISTINCT track_name) AS unique_tracks,
                       MIN(timestamp) AS first_play, MAX(timestamp) AS last_play,
                       SUM(CASE WHEN skipped = 1 THEN 1 ELSE 0 END) AS skip_count
                FROM listening_events WHERE {where}""",
            params,
        ).fetchone()
        monthly = connection.execute(
            f"""SELECT strftime('%Y-%m', timestamp) AS period, SUM(ms_played) AS total_ms,
                       COUNT(*) AS plays
                FROM listening_events WHERE {where}
                GROUP BY period ORDER BY period""",
            params,
        ).fetchall()
        top_tracks = connection.execute(
            f"""SELECT track_name, SUM(ms_played) AS total_ms, COUNT(*) AS play_count
                FROM listening_events WHERE {where}
                GROUP BY track_name ORDER BY total_ms DESC LIMIT 25""",
            params,
        ).fetchall()
    return {
        "entity": entity,
        "artist_name": artist,
        "name": name or artist,
        "stats": _result_with_hours(stats),
        "timeline": [_result_with_hours(row) for row in monthly],
        "top_tracks": [_result_with_hours(row) for row in top_tracks],
    }


def diagnostics(database: str) -> dict:
    with connect(database) as connection:
        counts = dict(
            connection.execute(
                """SELECT COUNT(*) AS events,
                          SUM(CASE WHEN album_name IS NULL THEN 1 ELSE 0 END) AS missing_albums,
                          SUM(CASE WHEN skipped IS NULL THEN 1 ELSE 0 END) AS unknown_skips,
                          COUNT(DISTINCT source_file) AS source_files
                   FROM listening_events"""
            ).fetchone()
        )
        runs = connection.execute(
            "SELECT details_json FROM import_runs ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return {"database": counts, "imports": [json.loads(row[0]) for row in runs]}


def years(database: str) -> list[int]:
    with connect(database) as connection:
        rows = connection.execute(
            "SELECT DISTINCT CAST(strftime('%Y', timestamp) AS INTEGER) AS year "
            "FROM listening_events ORDER BY year DESC"
        ).fetchall()
    return [row[0] for row in rows]


def _result_with_hours(row) -> dict:
    result = dict(row)
    if "total_ms" in result:
        result["hours"] = round((result["total_ms"] or 0) / 3_600_000, 2)
    return result


def _choose_granularity(start: str | None, end: str | None) -> str:
    if start and end:
        try:
            days = (datetime.fromisoformat(end[:10]) - datetime.fromisoformat(start[:10])).days
            if days <= 120:
                return "day"
            if days > 1_500:
                return "year"
        except ValueError:
            pass
    return "month"
