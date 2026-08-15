from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS listening_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_hash TEXT NOT NULL UNIQUE,
    timestamp TEXT NOT NULL,
    artist_name TEXT NOT NULL,
    track_name TEXT NOT NULL,
    album_name TEXT,
    spotify_track_uri TEXT,
    spotify_episode_uri TEXT,
    ms_played INTEGER NOT NULL CHECK (ms_played >= 0),
    platform TEXT,
    country TEXT,
    shuffle INTEGER,
    skipped INTEGER,
    offline INTEGER,
    reason_start TEXT,
    reason_end TEXT,
    source_file TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON listening_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_artist ON listening_events(artist_name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_events_track ON listening_events(track_name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_events_album ON listening_events(album_name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS import_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    input_files INTEGER NOT NULL,
    accepted INTEGER NOT NULL,
    duplicates INTEGER NOT NULL,
    ignored INTEGER NOT NULL,
    warning_count INTEGER NOT NULL,
    details_json TEXT NOT NULL
);
"""


class ClosingConnection(sqlite3.Connection):
    """SQLite connection that closes when its context manager exits."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect(database: str) -> sqlite3.Connection:
    connection = sqlite3.connect(database, timeout=30, factory=ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def init_db(database: str) -> None:
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with connect(database) as connection:
        connection.executescript(SCHEMA)


@contextmanager
def transaction(database: str) -> Iterator[sqlite3.Connection]:
    connection = connect(database)
    try:
        connection.execute("BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
