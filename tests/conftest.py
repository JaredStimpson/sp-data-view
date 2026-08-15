from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.sqlite3"),
            "LOG_FILE": str(tmp_path / "test.log"),
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()

