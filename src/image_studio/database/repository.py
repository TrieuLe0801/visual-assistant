"""SQLite persistence for users and image operation history."""

from __future__ import annotations

import sqlite3
import uuid

from ..utils.time import utc_now
from .connection import SQLiteConnectionFactory
from .models import ImageRecord, User
from .schema import SCHEMA_SQL
from .settings import DatabaseSettings


class Database:
    def __init__(self, settings: DatabaseSettings) -> None:
        self.connections = SQLiteConnectionFactory(settings)

    def initialize(self) -> None:
        self.connections.initialize_directory()
        with self.connections.connect() as connection:
            connection.executescript(SCHEMA_SQL)
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
                """SELECT * FROM images WHERE owner_id = ?
                   ORDER BY created_at DESC, id DESC""",
                (owner_id,),
            ).fetchall()
        return [_image_from_row(row) for row in rows]

    def get_image(self, owner_id: str, image_id: str) -> ImageRecord | None:
        with self.connections.connect() as connection:
            row = connection.execute(
                "SELECT * FROM images WHERE owner_id = ? AND id = ?",
                (owner_id, image_id),
            ).fetchone()
        return _image_from_row(row)

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
