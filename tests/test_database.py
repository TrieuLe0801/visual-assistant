"""Database configuration and transaction boundary checks."""

from pathlib import Path

import pytest

from image_studio.database.connection import SQLiteConnectionFactory
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
