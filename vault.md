# Project Vault

This file is the durable working memory for the Spotify Listening Analytics project. Read it before making project changes and update it after every user prompt that changes requirements, architecture, setup, or known issues.

## How to use this vault

1. Read this file before planning or editing.
2. Add each new user request to **Prompt history** with the date and an actionable interpretation.
3. Update **Current decisions** when a requirement becomes an implementation choice.
4. Update **Project map** when important files, commands, or data flows change.
5. Record test results and unresolved problems in **Verification and known issues**.
6. Keep secrets, personal listening data, raw exports, database files, logs, and virtual environments out of Git.
7. Keep this concise and current; do not delete useful history unless it is superseded and the replacement is recorded.

## Current objective

Build a GitHub-ready Python MVP that imports Spotify JSON files or export ZIP archives, stores normalized events locally, and provides an interactive local web dashboard for overview statistics, rankings, timeline/calendar views, search, details, filtering, diagnostics, and local-data deletion.

## Current decisions

- Runtime: Python local web application.
- Privacy: listening history is processed and stored only on the user's machine.
- Persistence: SQLite in a Git-ignored local data directory.
- Frontend: responsive HTML/CSS/JavaScript served by the Python app; no account or cloud service.
- Import formats: Spotify extended streaming-history and legacy streaming-history JSON, either as individual files or in ZIP archives.
- Windows workflow: `setup.bat` creates `.venv` and installs dependencies; `launch.bat` starts the app.
- Debug workflow: structured rotating logs, a diagnostics page/API, health checks, a database inspection CLI, `debug.bat`, and automated tests.
- Repository: README, license, contribution guidance, environment example, tests, and `.gitignore` suitable for GitHub.

## Data-handling rules

- Never commit files in `data/`, Spotify export archives, raw JSON histories, logs, or generated normalized exports.
- Validate archive members and reject unsafe ZIP paths.
- Do not silently discard invalid records; count them and expose warnings in import diagnostics.
- Deduplicate events deterministically while preserving legitimate repeated listens.
- Treat optional Spotify fields as optional and display missing metadata gracefully.

## Project map

- `README.md` — user setup, Spotify export guidance, privacy notes, commands, and repository tour.
- `docs/PRODUCT_PLAN.md` — the complete supplied product and implementation roadmap, preserved as UTF-8 Markdown for GitHub.
- `docs/IMPLEMENTATION.md` — implemented Python architecture, normalization decisions, API, and next milestones.
- `app/importer.py` — ZIP/JSON inspection, Spotify schema detection, normalization, validation, and deduplication.
- `app/db.py` — SQLite schema, indexes, transactions, and connection lifecycle.
- `app/analytics.py` — reusable analytics query layer and date filtering.
- `app/routes.py` — dashboard routes, JSON APIs, CSV export, and confirmed deletion.
- `app/templates/index.html`, `app/static/` — responsive local dashboard with overview, top explorer, heatmap/timeline, search, details, import, and diagnostics.
- `setup.bat` — creates `.venv` and installs `requirements-dev.txt`.
- `launch.bat` — runs the Waitress local server and opens the browser.
- `debug.bat`, `tools/diagnostics.py` — integrity/package/data/log checks plus debug launch.
- `sample_data/spotify_extended_sample.json` — eight synthetic Spotify-format events for safe demos.
- `tests/` — importer, ZIP safety, API, analytics, diagnostic-error, export, and deletion tests.
- `outputs/NEW_CHAT_STARTUP_PLAN.md` — reusable checklist and `vault.md` template for organizing future project chats.

Primary commands:

```text
setup.bat
launch.bat
debug.bat
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
```

## Verification and known issues

- 2026-08-15: 10 automated tests pass on Python 3.12.13.
- 2026-08-15: Ruff lint passes and browser JavaScript passes `node --check`.
- 2026-08-15: End-to-end synthetic import accepted 8/8 events, returned the correct top artist and artist details, and exported successfully.
- 2026-08-15: Live Waitress smoke test passed (`/api/health` = `ok`, dashboard HTTP 200).
- 2026-08-15: SQLite connections use a closing context wrapper to prevent Windows file locks and long-session connection buildup.
- Current MVP limitation: each JSON file is parsed into memory; a future version should add streaming JSON and background progress for individual multi-gigabyte files.
- Current metadata limitation: legacy Spotify exports may omit album, skip, shuffle, and offline values; these remain unknown rather than inferred.
- The repository is initialized on branch `main`; no commit or remote has been created.

## Prompt history

### 2026-08-15 — Initial build request

User supplied `spotify_listening_analytics_app_plan.md` and requested:

- Use a vault strategy for effective context/usage management.
- Create `vault.md` in the working directory first, store important notes from every prompt, and explain how to maintain it.
- Turn the supplied plan into a GitHub-compatible project.
- Implement in Python.
- Include a Windows setup batch file that creates a virtual environment.
- Include a Windows launch batch file.
- Add debugging tools.
- Ensure the app works with Spotify-provided listening-history data.

Implementation interpretation: deliver a functional local MVP rather than only rewriting the plan, while preserving the supplied product roadmap in project documentation.

### 2026-08-17 — New-chat organization guide

User requested a simple but complete Markdown plan explaining how to start and organize future chats, including how to create and maintain `vault.md`.

Implementation interpretation: provide a reusable startup checklist, recommended directory structure, ready-to-copy vault template, opening prompt, working rules, and end-of-chat handoff routine.
