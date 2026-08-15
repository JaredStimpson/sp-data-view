# Contributing

Thanks for helping improve Resonance.

## Development workflow

1. Read `vault.md` and `docs/IMPLEMENTATION.md` before changing behavior.
2. Run `setup.bat`, or create `.venv` and install `requirements-dev.txt` manually.
3. Create a focused branch.
4. Add or update tests with code changes.
5. Run `python -m pytest` and `python -m ruff check .`.
6. Update `vault.md` when requirements, architecture, commands, or known issues change.

Use only synthetic fixtures. Real listening exports contain personal behavioral data and must never be committed, attached to issues, or copied into logs.

## Pull requests

Describe the user-facing effect, data-model changes, verification performed, and any migration or privacy impact. Keep SQL in `app/analytics.py`, parsing/normalization in `app/importer.py`, and presentation in `app/static` or `app/templates`.

