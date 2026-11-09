"""Database configuration and transaction boundary checks."""

import sqlite3
from pathlib import Path

import pytest

from image_studio.database.connection import SQLiteConnectionFactory
from image_studio.database.repository import Database
from image_studio.database.schema import SCHEMA_SQL
from image_studio.database.settings import DatabaseSettings


def test_database_path_is_loaded_from_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "configured.sqlite3"
    monkeypatch.setenv("IMAGE_DATABASE_PATH", str(path))

    assert DatabaseSettings.from_env().path == path


def test_connection_rolls_back_and_enables_foreign_keys(tmp_path: Path) -> None:
    connections = SQLiteConnectionFactory(DatabaseSettings(tmp_path / "db" / "test.db"))
    connections.initialize_directory()
    with connections.connect() as connection:
        connection.execute("CREATE TABLE example (value TEXT NOT NULL)")
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1

    with (
        pytest.raises(RuntimeError, match="abort"),
        connections.connect() as connection,
    ):
        connection.execute("INSERT INTO example (value) VALUES ('discard')")
        raise RuntimeError("abort")

    with connections.connect() as connection:
        assert connection.execute("SELECT value FROM example").fetchall() == []


def test_existing_image_database_gets_deletion_column(tmp_path: Path) -> None:
    settings = DatabaseSettings(tmp_path / "existing.sqlite3")
    old_schema = SCHEMA_SQL.replace("error TEXT,\n    deleted_at TEXT", "error TEXT")
    assert old_schema != SCHEMA_SQL
    with sqlite3.connect(settings.path) as connection:
        connection.executescript(old_schema)

    database = Database(settings)
    database.initialize()
    database.initialize()
    with database.connections.connect() as connection:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(images)")
        }
    assert "deleted_at" in columns
