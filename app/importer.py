from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import BinaryIO, Iterable

from .db import transaction

MAX_ARCHIVE_MEMBERS = 5_000
MAX_MEMBER_BYTES = 1_000_000_000
MAX_ARCHIVE_BYTES = 5_000_000_000


@dataclass
class FileDiagnostic:
    filename: str
    status: str
    format: str = "unknown"
    records_found: int = 0
    accepted: int = 0
    duplicates: int = 0
    ignored: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ImportReport:
    started_at: str
    finished_at: str = ""
    input_files: int = 0
    accepted: int = 0
    duplicates: int = 0
    ignored: int = 0
    files: list[FileDiagnostic] = field(default_factory=list)

    @property
    def warning_count(self) -> int:
        return sum(len(item.warnings) for item in self.files)

    def to_dict(self) -> dict:
        result = asdict(self)
        result["warning_count"] = self.warning_count
        return result


def import_uploads(database: str, uploads: Iterable) -> ImportReport:
    report = ImportReport(started_at=_utc_now())
    with transaction(database) as connection:
        for upload in uploads:
            filename = upload.filename or "unnamed"
            lower = filename.lower()
            try:
                if lower.endswith(".zip"):
                    _import_zip(connection, upload.stream, filename, report)
                elif lower.endswith(".json"):
                    report.input_files += 1
                    diagnostic = _import_json_stream(
                        connection, upload.stream, filename, source_container=None
                    )
                    report.files.append(diagnostic)
                else:
                    report.input_files += 1
                    report.files.append(
                        FileDiagnostic(
                            filename=filename,
                            status="unsupported",
                            warnings=["Only .zip and .json files are supported."],
                        )
                    )
            except (
                OSError,
                UnicodeError,
                ValueError,
                json.JSONDecodeError,
                zipfile.BadZipFile,
            ) as error:
                report.files.append(
                    FileDiagnostic(filename=filename, status="error", warnings=[str(error)])
                )

        report.finished_at = _utc_now()
        for item in report.files:
            report.accepted += item.accepted
            report.duplicates += item.duplicates
            report.ignored += item.ignored
        payload = json.dumps(report.to_dict(), ensure_ascii=False)
        connection.execute(
            """INSERT INTO import_runs
               (started_at, finished_at, input_files, accepted, duplicates, ignored,
                warning_count, details_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                report.started_at,
                report.finished_at,
                report.input_files,
                report.accepted,
                report.duplicates,
                report.ignored,
                report.warning_count,
                payload,
            ),
        )
    return report


def _import_zip(connection: sqlite3.Connection, stream: BinaryIO, archive_name: str,
                report: ImportReport) -> None:
    try:
        archive = zipfile.ZipFile(stream)
    except zipfile.BadZipFile as error:
        raise ValueError(f"{archive_name} is not a valid ZIP archive.") from error

    members = archive.infolist()
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise ValueError(f"Archive has more than {MAX_ARCHIVE_MEMBERS:,} members.")
    total_size = sum(member.file_size for member in members)
    if total_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Archive expands beyond the 5 GB safety limit.")

    json_members = []
    for member in members:
        path = PurePosixPath(member.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts:
            report.files.append(
                FileDiagnostic(
                    filename=f"{archive_name}:{member.filename}",
                    status="unsafe",
                    warnings=["Unsafe archive path was rejected."],
                )
            )
            continue
        if member.is_dir() or not member.filename.lower().endswith(".json"):
            continue
        if member.file_size > MAX_MEMBER_BYTES:
            report.files.append(
                FileDiagnostic(
                    filename=f"{archive_name}:{member.filename}",
                    status="too_large",
                    warnings=["JSON member exceeds the 1 GB safety limit."],
                )
            )
            continue
        json_members.append(member)

    if not json_members:
        report.files.append(
            FileDiagnostic(
                filename=archive_name,
                status="unsupported",
                warnings=["No JSON files were found in the ZIP archive."],
            )
        )
        return

    for member in json_members:
        report.input_files += 1
        with archive.open(member) as raw:
            diagnostic = _import_json_stream(
                connection,
                io.TextIOWrapper(raw, encoding="utf-8-sig"),
                member.filename,
                source_container=archive_name,
            )
            report.files.append(diagnostic)


def _import_json_stream(connection: sqlite3.Connection, stream: BinaryIO,
                        filename: str, source_container: str | None) -> FileDiagnostic:
    diagnostic = FileDiagnostic(filename=filename, status="parsed")
    source = f"{source_container}:{filename}" if source_container else filename
    if isinstance(stream, io.TextIOBase):
        payload = json.load(stream)
    else:
        payload = json.load(io.TextIOWrapper(stream, encoding="utf-8-sig"))

    records = _find_record_list(payload)
    if records is None:
        diagnostic.status = "unsupported"
        diagnostic.warnings.append("JSON does not contain a recognized Spotify event list.")
        return diagnostic
    diagnostic.records_found = len(records)
    if not records:
        diagnostic.status = "empty"
        diagnostic.warnings.append("The file contains no listening events.")
        return diagnostic

    diagnostic.format = _detect_format(records[0])
    if diagnostic.format == "unknown":
        diagnostic.status = "unsupported"
        diagnostic.ignored = len(records)
        diagnostic.warnings.append("Spotify event fields were not recognized.")
        return diagnostic

    missing_examples: list[str] = []
    for index, raw in enumerate(records):
        event, warning = normalize_event(raw, source)
        if event is None:
            diagnostic.ignored += 1
            if warning and len(missing_examples) < 5:
                missing_examples.append(f"Record {index + 1}: {warning}")
            continue
        columns = ", ".join(event)
        placeholders = ", ".join("?" for _ in event)
        try:
            connection.execute(
                f"INSERT INTO listening_events ({columns}) VALUES ({placeholders})",
                tuple(event.values()),
            )
            diagnostic.accepted += 1
        except sqlite3.IntegrityError as error:
            if "event_hash" in str(error):
                diagnostic.duplicates += 1
            else:
                diagnostic.ignored += 1
                if len(missing_examples) < 5:
                    missing_examples.append(f"Record {index + 1}: {error}")

    diagnostic.warnings.extend(missing_examples)
    if diagnostic.ignored > len(missing_examples):
        diagnostic.warnings.append(
            f"{diagnostic.ignored - len(missing_examples)} additional invalid records were ignored."
        )
    diagnostic.status = "imported" if diagnostic.accepted or diagnostic.duplicates else "no_events"
    return diagnostic


def _find_record_list(payload) -> list[dict] | None:
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "events", "history", "plays"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value
    return None


def _detect_format(record: dict) -> str:
    if "ts" in record and ("ms_played" in record or "master_metadata_track_name" in record):
        return "spotify_extended"
    if "endTime" in record and ("msPlayed" in record or "trackName" in record):
        return "spotify_legacy"
    if "played_at" in record and "track" in record:
        return "spotify_web_api"
    return "unknown"


def normalize_event(raw: dict, source_file: str) -> tuple[dict | None, str | None]:
    event_format = _detect_format(raw)
    if event_format == "spotify_extended":
        timestamp = raw.get("ts")
        artist = raw.get("master_metadata_album_artist_name") or raw.get("episode_show_name")
        track = raw.get("master_metadata_track_name") or raw.get("episode_name")
        album = raw.get("master_metadata_album_album_name")
        ms_played = raw.get("ms_played")
        values = {
            "spotify_track_uri": raw.get("spotify_track_uri"),
            "spotify_episode_uri": raw.get("spotify_episode_uri"),
            "platform": raw.get("platform"),
            "country": raw.get("conn_country"),
            "shuffle": _optional_bool(raw.get("shuffle")),
            "skipped": _optional_bool(raw.get("skipped")),
            "offline": _optional_bool(raw.get("offline")),
            "reason_start": raw.get("reason_start"),
            "reason_end": raw.get("reason_end"),
        }
    elif event_format == "spotify_legacy":
        timestamp = raw.get("endTime")
        artist = raw.get("artistName")
        track = raw.get("trackName")
        album = raw.get("albumName")
        ms_played = raw.get("msPlayed")
        values = {
            "spotify_track_uri": raw.get("spotifyTrackUri"),
            "spotify_episode_uri": raw.get("spotifyEpisodeUri"),
            "platform": raw.get("platform"),
            "country": raw.get("country"),
            "shuffle": _optional_bool(raw.get("shuffle")),
            "skipped": _optional_bool(raw.get("skipped")),
            "offline": _optional_bool(raw.get("offline")),
            "reason_start": raw.get("reasonStart"),
            "reason_end": raw.get("reasonEnd"),
        }
    elif event_format == "spotify_web_api":
        track_data = raw.get("track") or {}
        artists = track_data.get("artists") or []
        timestamp = raw.get("played_at")
        artist = artists[0].get("name") if artists else None
        track = track_data.get("name")
        album_data = track_data.get("album") or {}
        album = album_data.get("name")
        ms_played = track_data.get("duration_ms", 0)
        values = {
            "spotify_track_uri": track_data.get("uri"),
            "spotify_episode_uri": None,
            "platform": None,
            "country": None,
            "shuffle": None,
            "skipped": None,
            "offline": None,
            "reason_start": None,
            "reason_end": None,
        }
    else:
        return None, "unrecognized event fields"

    parsed_timestamp = _parse_timestamp(timestamp)
    if parsed_timestamp is None:
        return None, "missing or invalid timestamp"
    if not isinstance(artist, str) or not artist.strip():
        return None, "missing artist/show name"
    if not isinstance(track, str) or not track.strip():
        return None, "missing track/episode name"
    try:
        milliseconds = max(0, int(ms_played))
    except (TypeError, ValueError):
        return None, "missing or invalid played duration"

    canonical = "\x1f".join(
        [
            parsed_timestamp,
            artist.strip(),
            track.strip(),
            str(album or ""),
            str(milliseconds),
            str(values.get("spotify_track_uri") or values.get("spotify_episode_uri") or ""),
        ]
    )
    return {
        "event_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "timestamp": parsed_timestamp,
        "artist_name": artist.strip(),
        "track_name": track.strip(),
        "album_name": album.strip() if isinstance(album, str) and album.strip() else None,
        **values,
        "ms_played": milliseconds,
        "source_file": source_file,
    }, None


def _parse_timestamp(value) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        if text.endswith("Z"):
            parsed = datetime.fromisoformat(text[:-1] + "+00:00")
        else:
            parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        parsed = parsed.astimezone(timezone.utc)
        return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")
    except ValueError:
        return None


def _optional_bool(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, str):
        return 1 if value.lower() in {"true", "1", "yes"} else 0
    return 1 if bool(value) else 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
