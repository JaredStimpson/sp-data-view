from __future__ import annotations

import argparse
import importlib.metadata
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = ROOT / "data" / "listening_history.sqlite3"
DEFAULT_LOG = ROOT / "logs" / "app.log"


def inspect(database: Path, log_file: Path) -> tuple[dict, bool]:
    report: dict = {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "database": str(database),
        "database_exists": database.exists(),
        "packages": {},
        "checks": {},
    }
    healthy = True
    for package in ("Flask", "waitress", "pytest"):
        try:
            report["packages"][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            report["packages"][package] = "not installed"
            if package in {"Flask", "waitress"}:
                healthy = False

    if database.exists():
        try:
            with sqlite3.connect(database) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                report["checks"]["sqlite_integrity"] = integrity
                healthy = healthy and integrity == "ok"
                tables = {
                    row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                required = {"listening_events", "import_runs"}
                report["checks"]["schema"] = (
                    "ok" if required.issubset(tables) else f"missing: {sorted(required - tables)}"
                )
                healthy = healthy and required.issubset(tables)
                if "listening_events" in tables:
                    row = connection.execute(
                        """SELECT COUNT(*) AS events, COUNT(DISTINCT source_file) AS files,
                                  MIN(timestamp) AS first_play, MAX(timestamp) AS last_play
                           FROM listening_events"""
                    ).fetchone()
                    report["data"] = {
                        "events": row[0], "source_files": row[1],
                        "first_play": row[2], "last_play": row[3]
                    }
        except sqlite3.Error as error:
            report["checks"]["database_error"] = str(error)
            healthy = False
    else:
        report["checks"]["database"] = "not created yet; it will be created on first launch"

    if log_file.exists():
        try:
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            report["recent_log"] = lines[-10:]
        except OSError as error:
            report["recent_log"] = [f"Could not read log: {error}"]
    else:
        report["recent_log"] = []
    return report, healthy


def print_human(report: dict, healthy: bool) -> None:
    print("Resonance local diagnostics")
    print("=" * 29)
    print(f"Status: {'HEALTHY' if healthy else 'NEEDS ATTENTION'}")
    print(f"Python: {report['python']} ({report['python_executable']})")
    print("Packages: " + ", ".join(f"{key} {value}" for key, value in report["packages"].items()))
    print(f"Database: {report['database']}")
    for key, value in report["checks"].items():
        print(f"  {key}: {value}")
    if report.get("data"):
        print("Data: " + ", ".join(f"{key}={value}" for key, value in report["data"].items()))
    if report["recent_log"]:
        print("Recent log lines:")
        for line in report["recent_log"]:
            print(f"  {line}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the local Resonance installation.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()
    report, healthy = inspect(args.database.resolve(), args.log.resolve())
    if args.json:
        print(json.dumps({**report, "healthy": healthy}, indent=2))
    else:
        print_human(report, healthy)
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())

