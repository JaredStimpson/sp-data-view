from __future__ import annotations

import io
import json

EVENTS = [
    {
        "ts": "2024-01-02T10:00:00Z", "ms_played": 180000,
        "master_metadata_album_artist_name": "Alpha", "master_metadata_track_name": "First",
        "master_metadata_album_album_name": "One", "spotify_track_uri": "spotify:track:1"
    },
    {
        "ts": "2024-02-03T11:00:00Z", "ms_played": 240000,
        "master_metadata_album_artist_name": "Beta", "master_metadata_track_name": "Second",
        "master_metadata_album_album_name": "Two", "spotify_track_uri": "spotify:track:2"
    },
    {
        "ts": "2025-03-04T12:00:00Z", "ms_played": 120000,
        "master_metadata_album_artist_name": "Alpha", "master_metadata_track_name": "Third",
        "master_metadata_album_album_name": "One", "spotify_track_uri": "spotify:track:3"
    },
]


def import_events(client):
    return client.post(
        "/api/import",
        data={"files": (io.BytesIO(json.dumps(EVENTS).encode()), "history.json")},
        content_type="multipart/form-data",
    )


def test_health_and_empty_summary(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}
    assert client.get("/api/summary").get_json()["plays"] == 0


def test_import_summary_filters_and_rankings(client):
    response = import_events(client)
    assert response.status_code == 200
    assert response.get_json()["accepted"] == 3
    summary = client.get("/api/summary").get_json()
    assert summary["plays"] == 3
    assert summary["unique_artists"] == 2
    filtered = client.get("/api/summary?start=2024-01-01&end=2024-12-31").get_json()
    assert filtered["plays"] == 2
    top = client.get("/api/top?entity=artists&metric=time&limit=10").get_json()
    assert top[0]["artist_name"] == "Alpha"
    assert top[0]["play_count"] == 2


def test_search_timeline_diagnostics_and_export(client):
    import_events(client)
    assert client.get("/api/search?q=alp").get_json()["artists"][0]["artist_name"] == "Alpha"
    assert len(client.get("/api/timeline?granularity=year").get_json()) == 2
    diagnostics = client.get("/api/diagnostics").get_json()
    assert diagnostics["database"]["events"] == 3
    export = client.get("/api/export.csv")
    assert export.status_code == 200
    assert b"Alpha" in export.data


def test_delete_requires_confirmation(client):
    import_events(client)
    assert client.delete("/api/data", json={}).status_code == 400
    response = client.delete("/api/data", json={"confirm": "DELETE"})
    assert response.get_json()["deleted"] == 3
    assert client.get("/api/summary").get_json()["plays"] == 0


def test_bad_json_is_reported_in_import_diagnostics(client):
    response = client.post(
        "/api/import",
        data={"files": (io.BytesIO(b"not json"), "broken.json")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 422
    report = response.get_json()
    assert report["accepted"] == 0
    assert report["files"][0]["status"] == "error"
