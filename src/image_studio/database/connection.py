"""Short-lived SQLite connections and transaction boundaries."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from .settings import DatabaseSettings


class SQLiteConnectionFactory:
    def __init__(self, settings: DatabaseSettings) -> None:
        self.settings = settings

    def initialize_directory(self) -> None:
        if str(self.settings.path) != ":memory:":
            self.settings.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            str(self.settings.path), timeout=self.settings.timeout_seconds
        )
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
