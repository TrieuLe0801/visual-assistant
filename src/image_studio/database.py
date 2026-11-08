"""SQLite persistence for users and image operation history."""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@dataclass(frozen=True)
class User:
    id: str
    email: str
    password_hash: str
    created_at: str


@dataclass(frozen=True)
class ImageRecord:
    id: str
    owner_id: str
    prompt: str
    operation: str
    status: str
    parent_id: str | None
    created_at: str
    provider: str
    model: str
    file_path: str | None
    mime_type: str | None
    size_bytes: int | None
    error: str | None


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS images (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    prompt TEXT NOT NULL,
                    operation TEXT NOT NULL CHECK (
                        operation IN ('generate', 'edit', 'variation')
                    ),
                    status TEXT NOT NULL CHECK (
                        status IN ('processing', 'succeeded', 'failed')
                    ),
                    parent_id TEXT REFERENCES images(id),
                    created_at TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    file_path TEXT,
                    mime_type TEXT,
                    size_bytes INTEGER,
                    error TEXT
                );
                CREATE INDEX IF NOT EXISTS images_owner_created
                    ON images(owner_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS images_parent
                    ON images(parent_id);
                """)
            connection.execute("""UPDATE images SET status = 'failed',
                   error = 'Operation interrupted before completion.'
                   WHERE status = 'processing'""")

    def create_user(self, email: str, password_hash: str) -> User:
        user = User(uuid.uuid4().hex, email, password_hash, utc_now())
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO users (id, email, password_hash, created_at) "
                "VALUES (?, ?, ?, ?)",
                (user.id, user.email, user.password_hash, user.created_at),
            )
        return user

    def get_user_by_email(self, email: str) -> User | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash, created_at "
                "FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        return _user_from_row(row)

    def get_user_by_id(self, user_id: str) -> User | None:
        with self._connect() as connection:
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
        with self._connect() as connection:
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
        with self._connect() as connection:
            connection.execute(
                """UPDATE images SET status = 'succeeded', file_path = ?,
                   mime_type = ?, size_bytes = ?, error = NULL WHERE id = ?""",
                (file_path, mime_type, size_bytes, image_id),
            )

    def mark_image_failed(self, image_id: str, error: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE images SET status = 'failed', error = ? WHERE id = ?",
                (error[:500], image_id),
            )

    def list_images(self, owner_id: str) -> list[ImageRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM images WHERE owner_id = ?
                   ORDER BY created_at DESC, id DESC""",
                (owner_id,),
            ).fetchall()
        return [_image_from_row(row) for row in rows]

    def get_image(self, owner_id: str, image_id: str) -> ImageRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM images WHERE owner_id = ? AND id = ?",
                (owner_id, image_id),
            ).fetchone()
        return _image_from_row(row)

    def close(self) -> None:
        return None

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(str(self.path), timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


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
