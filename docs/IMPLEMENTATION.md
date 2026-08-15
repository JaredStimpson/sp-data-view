# Implementation notes

## MVP architecture

```text
Spotify ZIP / JSON
        |
        v
Format detection and normalization (`app/importer.py`)
        |
        v
Local SQLite database (`data/listening_history.sqlite3`)
        |
        v
Analytics query layer (`app/analytics.py`)
        |
        v
Flask JSON API + local dashboard
```

The supplied product plan recommends a React/DuckDB browser application. This repository uses Python, as requested, while retaining the central privacy principle: files are processed locally and the server listens on loopback by default. SQLite provides reliable persistence and fast indexed queries for an MVP without requiring a separate database service.

## Normalization

Every valid record becomes a row in `listening_events`. Required fields are UTC timestamp, artist/show name, track/episode name, and non-negative played milliseconds. Album, URI, platform, country, skip, shuffle, offline, and start/end reason fields remain nullable.

An event hash is computed from timestamp, artist, track, album, played duration, and Spotify URI. The hash has a unique constraint, so importing overlapping files reports duplicates without adding duplicate rows. This may collapse two genuinely identical records with the same timestamp and duration; Spotify's timestamp resolution makes that rare and the behavior is deterministic.

Legacy timestamps without an offset are interpreted as UTC. Modern `ts` timestamps retain their instant and are normalized to UTC.

## Import diagnostics

Each import stores a compact JSON report in `import_runs`, including format, record counts, ignored rows, duplicates, and up to five representative validation warnings per file. The UI exposes the 20 latest runs. The diagnostics CLI also checks SQLite integrity and reports missing optional metadata.

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Server/database health |
| `POST` | `/api/import` | Multipart ZIP/JSON import (`files`) |
| `GET` | `/api/summary` | Period summary |
| `GET` | `/api/top` | Artist, track, or album rankings |
| `GET` | `/api/timeline` | Day/month/year aggregation |
| `GET` | `/api/calendar` | Daily heatmap values |
| `GET` | `/api/search?q=` | Artist, track, and album search |
| `GET` | `/api/entity/<type>` | Entity detail and monthly timeline |
| `GET` | `/api/diagnostics` | Database and import diagnostics |
| `GET` | `/api/years` | Imported calendar years |
| `GET` | `/api/export.csv` | Normalized local CSV export |
| `DELETE` | `/api/data` | Confirmed local-data deletion |

Analytics endpoints accept optional `start=YYYY-MM-DD` and `end=YYYY-MM-DD`. The end date is inclusive in the user interface and converted to an exclusive next-day bound in SQL.

## Next milestones

1. Stream very large JSON inputs with `ijson` and background import jobs.
2. Precompute aggregates after import and benchmark 500,000+ events.
3. Add session, skip/completion, listening-clock, discovery, and comparison analytics.
4. Add album detail navigation and richer accessible chart interaction.
5. Package with Tauri or PyInstaller for users without Python.
6. Add an opt-in metadata enrichment system with explicit network/privacy controls.

