"""Persisted account and image metadata contracts."""

from dataclasses import dataclass


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
