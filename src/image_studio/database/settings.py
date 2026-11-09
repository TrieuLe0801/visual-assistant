"""SQLite configuration kept separate from provider and web settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatabaseSettings:
    path: Path
    timeout_seconds: float = 15.0

    @classmethod
    def from_env(cls) -> DatabaseSettings:
        return cls(path=Path(os.getenv("IMAGE_DATABASE_PATH", "var/image-studio.db")))
