"""SQLite schema for account and image operation records."""

SCHEMA_SQL = """
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
    operation TEXT NOT NULL CHECK (operation IN ('generate', 'edit', 'variation')),
    status TEXT NOT NULL CHECK (status IN ('processing', 'succeeded', 'failed')),
    parent_id TEXT REFERENCES images(id),
    created_at TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    file_path TEXT,
    mime_type TEXT,
    size_bytes INTEGER,
    error TEXT,
    deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS images_owner_created
    ON images(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS images_parent
    ON images(parent_id);
"""
