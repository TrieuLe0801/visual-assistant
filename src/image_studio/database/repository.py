"""SQLite persistence for users and image operation history."""

from __future__ import annotations

import sqlite3
import time
import uuid

from ..utils.time import utc_now
from .connection import SQLiteConnectionFactory
from .models import ImageRecord, User
from .schema import SCHEMA_SQL
from .settings import DatabaseSettings


class RateLimitExceeded(Exception):
    """A request exceeds an atomic, persistent application limit."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("Request limit reached.")
        self.retry_after = retry_after


class Database:
    def __init__(self, settings: DatabaseSettings) -> None:
        self.connections = SQLiteConnectionFactory(settings)

    def initialize(self) -> None:
        self.connections.initialize_directory()
        with self.connections.connect() as connection:
            connection.executescript(SCHEMA_SQL)
            columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(images)")
            }
            if "deleted_at" not in columns:
                connection.execute("ALTER TABLE images ADD COLUMN deleted_at TEXT")
            connection.execute("""UPDATE images SET status = 'failed',
                   error = 'Operation interrupted before completion.'
                   WHERE status = 'processing'""")

    def create_user(self, email: str, password_hash: str) -> User:
        user = User(uuid.uuid4().hex, email, password_hash, utc_now())
        with self.connections.connect() as connection:
            connection.execute(
                "INSERT INTO users (id, email, password_hash, created_at) "
                "VALUES (?, ?, ?, ?)",
                (user.id, user.email, user.password_hash, user.created_at),
            )
        return user

    def get_user_by_email(self, email: str) -> User | None:
        with self.connections.connect() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash, created_at "
                "FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        return _user_from_row(row)

    def get_user_by_id(self, user_id: str) -> User | None:
        with self.connections.connect() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return _user_from_row(row)

    def create_image_operation(
        self,
        *,
        owner_id: str,
        prompt: str,
        operation: str,
        parent_id: str | None,
        provider: str,
        model: str,
    ) -> ImageRecord:
        record = ImageRecord(
            id=uuid.uuid4().hex,
            owner_id=owner_id,
            prompt=prompt,
            operation=operation,
            status="processing",
            parent_id=parent_id,
            created_at=utc_now(),
            provider=provider,
            model=model,
            file_path=None,
            mime_type=None,
            size_bytes=None,
            error=None,
        )
        with self.connections.connect() as connection:
            connection.execute(
                """INSERT INTO images
                (id, owner_id, prompt, operation, status, parent_id, created_at,
                 provider, model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.id,
                    record.owner_id,
                    record.prompt,
                    record.operation,
                    record.status,
                    record.parent_id,
                    record.created_at,
                    record.provider,
                    record.model,
                ),
            )
        return record

    def mark_image_succeeded(
        self,
        image_id: str,
        *,
        file_path: str,
        mime_type: str,
        size_bytes: int,
    ) -> None:
        with self.connections.connect() as connection:
            connection.execute(
                """UPDATE images SET status = 'succeeded', file_path = ?,
                   mime_type = ?, size_bytes = ?, error = NULL WHERE id = ?""",
                (file_path, mime_type, size_bytes, image_id),
            )

    def mark_image_failed(self, image_id: str, error: str) -> None:
        with self.connections.connect() as connection:
            connection.execute(
                "UPDATE images SET status = 'failed', error = ? WHERE id = ?",
                (error[:500], image_id),
            )

    def list_images(self, owner_id: str) -> list[ImageRecord]:
        with self.connections.connect() as connection:
            rows = connection.execute(
                """SELECT * FROM images WHERE owner_id = ? AND deleted_at IS NULL
                   ORDER BY created_at DESC, id DESC""",
                (owner_id,),
            ).fetchall()
        return [_image_from_row(row) for row in rows]

    def get_image(self, owner_id: str, image_id: str) -> ImageRecord | None:
        with self.connections.connect() as connection:
            row = connection.execute(
                "SELECT * FROM images WHERE owner_id = ? AND id = ? "
                "AND deleted_at IS NULL",
                (owner_id, image_id),
            ).fetchone()
        return _image_from_row(row)

    def delete_image(self, owner_id: str, image_id: str) -> bool:
        with self.connections.connect() as connection:
            result = connection.execute(
                "UPDATE images SET deleted_at = ?, file_path = NULL "
                "WHERE owner_id = ? AND id = ? AND deleted_at IS NULL",
                (utc_now(), owner_id, image_id),
            )
        return result.rowcount == 1

    def consume_limits(
        self,
        rules: tuple[tuple[str, int, int], ...],
        *,
        now: int | None = None,
    ) -> None:
        """Consume all limits together so a rejected request consumes none."""
        current = int(time.time()) if now is None else now
        with self.connections.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            pending = []
            for key, maximum, window_seconds in rules:
                window_start = current - current % window_seconds
                row = connection.execute(
                    "SELECT window_start, hits FROM request_limits WHERE key = ?",
                    (key,),
                ).fetchone()
                hits = row["hits"] if row and row["window_start"] == window_start else 0
                if hits >= maximum:
                    raise RateLimitExceeded(window_seconds - (current - window_start))
                pending.append((key, window_start, hits + 1))
            for key, window_start, hits in pending:
                connection.execute(
                    """INSERT INTO request_limits (key, window_start, hits)
                    VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET
                    window_start = excluded.window_start, hits = excluded.hits""",
                    (key, window_start, hits),
                )
            connection.execute(
                "DELETE FROM request_limits WHERE window_start < ?",
                (current - 86400,),
            )

    def close(self) -> None:
        return None


def _user_from_row(row: sqlite3.Row | None) -> User | None:
    if row is None:
        return None
    return User(row["id"], row["email"], row["password_hash"], row["created_at"])


def _image_from_row(row: sqlite3.Row | None) -> ImageRecord | None:
    if row is None:
        return None
    return ImageRecord(
        id=row["id"],
        owner_id=row["owner_id"],
        prompt=row["prompt"],
        operation=row["operation"],
        status=row["status"],
        parent_id=row["parent_id"],
        created_at=row["created_at"],
        provider=row["provider"],
        model=row["model"],
        file_path=row["file_path"],
        mime_type=row["mime_type"],
        size_bytes=row["size_bytes"],
        error=row["error"],
    )
