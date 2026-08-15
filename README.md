# Resonance — Spotify Listening Analytics

A private, local web dashboard for exploring a Spotify listening-history export. Import Spotify's ZIP or JSON files, then explore lifetime totals, top artists/tracks/albums, date ranges, timelines, a daily heatmap, search, and entity details.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-b9ff66)
![Privacy](https://img.shields.io/badge/data-local%20only-b9ff66)

## What works in v0.1

- Import a Spotify export ZIP or one or more JSON files.
- Recognize extended streaming history (`ts`, `ms_played`, `master_metadata_*`) and legacy streaming history (`endTime`, `msPlayed`, `artistName`, `trackName`).
- Normalize and deduplicate overlapping exports in a local SQLite database.
- Filter the dashboard and rankings by year or a custom date range.
- View total hours, plays, artists, tracks, top rankings, listening timeline, and daily heatmap.
- Search artists, tracks, and albums, then open detail views.
- Inspect accepted, duplicate, ignored, and unsupported records in diagnostics.
- Export normalized events to CSV or permanently delete local data.
- Run integrity checks and inspect logs with the included debugging tool.

The full product roadmap is in [docs/PRODUCT_PLAN.md](docs/PRODUCT_PLAN.md). The implemented architecture is described in [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md).

## Quick start on Windows

1. Install [Python 3.10 or newer](https://www.python.org/downloads/windows/) and select **Add Python to PATH** during installation.
2. Double-click `setup.bat`. It creates `.venv` and installs the app and development tools.
3. Double-click `launch.bat`.
4. The dashboard opens at `http://127.0.0.1:5000`.

If the browser does not open automatically, visit that address manually. To stop the server, close its terminal window or press `Ctrl+C`.

## Get your Spotify data

Request account data from Spotify's privacy/download page. For the most complete analytics, request **Extended streaming history**. Spotify may deliver a ZIP containing files such as:

```text
Spotify Extended Streaming History/
  Streaming_History_Audio_2023-2024_0.json
  Streaming_History_Audio_2024-2025_1.json
```

You can import the delivered ZIP directly. The older `StreamingHistory0.json` format is also supported. Podcast episodes are imported when Spotify supplies an episode/show name.

> Your listening history is processed by a web server bound to your own computer and stored in `data/listening_history.sqlite3`. The app makes no analytics, account, or listening-data network requests.

## Command-line setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python run.py
```

Environment settings can be copied from `.env.example` and set in your shell. The app does not load `.env` automatically, avoiding another runtime dependency.

## Debugging and tests

Run `debug.bat` to check Python and database health, print recent import/log information, and start the development server with detailed logging.

Individual commands:

```powershell
.\.venv\Scripts\python.exe tools\diagnostics.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
.\.venv\Scripts\python.exe -m ruff check .
```

Logs rotate under `logs/`. Private data, logs, exports, archives, and the virtual environment are excluded in `.gitignore`.

## Repository layout

```text
app/
  analytics.py       SQL-backed analytics queries
  importer.py        Spotify format detection and normalization
  routes.py          Page and JSON API routes
  static/            Browser UI, charts, and styles
  templates/         Main application shell
data/                Local SQLite data (Git-ignored)
docs/                Product plan and implementation notes
logs/                Rotating local logs (Git-ignored)
sample_data/         Synthetic, safe test history
tests/               Importer and API tests
tools/               Database/log diagnostics CLI
run.py               Development/production entry point
setup.bat            Creates the Windows virtual environment
launch.bat           Starts the local app
debug.bat            Runs checks and launches debug mode
vault.md             Durable project memory and update protocol
```

## Privacy and limitations

- This is local-first in deployment: Python reads the selected files on your machine and binds to `127.0.0.1` by default.
- Do not expose the server to a public network. There is no authentication because it is designed for loopback use.
- Spotify does not include album metadata or skip/shuffle flags in every export format. Missing values remain unknown rather than guessed.
- The MVP loads each JSON member into memory during import. Multi-gigabyte individual JSON files may require a future streaming parser.
- Web API recently-played JSON can be recognized, but Spotify's downloadable export is the primary supported input.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please use synthetic listening data in tests and bug reports—never commit a real Spotify export.

Spotify is a trademark of Spotify AB. This independent project is not affiliated with or endorsed by Spotify.

