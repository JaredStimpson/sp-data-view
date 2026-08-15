from __future__ import annotations

import io
import json
import zipfile

from werkzeug.datastructures import FileStorage

from app.db import connect, init_db
from app.importer import import_uploads, normalize_event


def extended_event(**overrides):
    event = {
        "ts": "2025-04-05T12:30:00Z",
        "ms_played": 201000,
        "master_metadata_album_artist_name": "Test Artist",
        "master_metadata_track_name": "Test Track",
        "master_metadata_album_album_name": "Test Album",
        "spotify_track_uri": "spotify:track:test",
        "skipped": False,
    }
    event.update(overrides)
    return event


def test_normalizes_extended_and_legacy_events():
    extended, warning = normalize_event(extended_event(), "extended.json")
    assert warning is None
    assert extended["timestamp"] == "2025-04-05T12:30:00Z"
    assert extended["artist_name"] == "Test Artist"
    assert extended["ms_played"] == 201000

    legacy, warning = normalize_event(
        {"endTime": "2021-01-02 03:04", "artistName": "Old Artist",
         "trackName": "Old Track", "msPlayed": 1000},
        "StreamingHistory0.json",
    )
    assert warning is None
    assert legacy["timestamp"] == "2021-01-02T03:04:00Z"
    assert legacy["artist_name"] == "Old Artist"


def test_invalid_event_returns_a_reason():
    event, warning = normalize_event(extended_event(ts="not-a-date"), "bad.json")
    assert event is None
    assert "timestamp" in warning


def test_imports_json_and_deduplicates(tmp_path):
    database = str(tmp_path / "history.sqlite3")
    init_db(database)
    payload = json.dumps([extended_event()]).encode()
    uploads = [
        FileStorage(stream=io.BytesIO(payload), filename="history.json"),
        FileStorage(stream=io.BytesIO(payload), filename="history-copy.json"),
    ]
    report = import_uploads(database, uploads)
    assert report.accepted == 1
    assert report.duplicates == 1
    with connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM listening_events").fetchone()[0] == 1


def test_imports_json_from_zip(tmp_path):
    database = str(tmp_path / "history.sqlite3")
    init_db(database)
    archive_bytes = io.BytesIO()
    with zipfile.ZipFile(archive_bytes, "w") as archive:
        archive.writestr(
            "Spotify Extended Streaming History/history.json",
            json.dumps([extended_event()]),
        )
        archive.writestr("readme.txt", "not history")
    archive_bytes.seek(0)
    report = import_uploads(
        database, [FileStorage(stream=archive_bytes, filename="spotify.zip")]
    )
    assert report.accepted == 1
    assert report.files[0].format == "spotify_extended"


def test_rejects_unsafe_zip_member(tmp_path):
    database = str(tmp_path / "history.sqlite3")
    init_db(database)
    archive_bytes = io.BytesIO()
    with zipfile.ZipFile(archive_bytes, "w") as archive:
        archive.writestr("../history.json", json.dumps([extended_event()]))
    archive_bytes.seek(0)
    report = import_uploads(
        database, [FileStorage(stream=archive_bytes, filename="unsafe.zip")]
    )
    assert report.accepted == 0
    assert report.files[0].status == "unsafe"
