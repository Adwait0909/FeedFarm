"""Run every test against a throw-away database and QR folder.

Several tests issue DELETE statements for farmers, farms and cows. Without this
fixture they run against the real cow_qr_demo.sqlite3 and erase its data.
"""
import os
import secrets
import sqlite3
import tempfile
from pathlib import Path

import pytest

# The veterinary directory database is opened when asgi.py is imported, so it has to be redirected
# before any test module imports it (conftest.py is loaded first).
_VET_TEST_DIR = Path(tempfile.mkdtemp(prefix="farm2feed-vet-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_VET_TEST_DIR / 'veterinary.sqlite3').as_posix()}"

import app
import marketplace_api


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    database = tmp_path / "test.sqlite3"
    qr_folder = tmp_path / "qr_codes"
    qr_folder.mkdir()
    monkeypatch.setattr(app, "DB_PATH", str(database))
    monkeypatch.setattr(app, "DB_TYPE", "sqlite")
    monkeypatch.setattr(app, "QR_FOLDER", str(qr_folder))
    # Cow photos and the marketplace JSON store/uploads must not be touched either.
    cow_uploads = tmp_path / "uploads"
    cow_uploads.mkdir()
    monkeypatch.setattr(app, "UPLOAD_FOLDER", str(cow_uploads))
    monkeypatch.setitem(app.app.config, "UPLOAD_FOLDER", str(cow_uploads))
    monkeypatch.setattr(marketplace_api, "DATA_FILE", tmp_path / "marketplace-data.json")
    monkeypatch.setattr(marketplace_api, "UPLOAD_FOLDER", tmp_path / "marketplace-uploads")
    # Existing tests post raw forms; tests/test_csrf.py switches this back on explicitly.
    monkeypatch.setitem(app.app.config, "CSRF_PROTECT", False)
    monkeypatch.delenv("FARM2FEED_DEMO_MODE", raising=False)
    # The first doctor account of every throw-away database gets a random password.
    monkeypatch.setenv("DOCTOR_PASSWORD", secrets.token_urlsafe(16))
    conn = sqlite3.connect(database)
    try:
        app.ensure_sqlite_schema(conn)
    finally:
        conn.close()
    yield
