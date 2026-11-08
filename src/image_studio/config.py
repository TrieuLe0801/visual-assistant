"""Runtime settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_path: Path
    image_storage_path: Path
    provider_name: str
    model_name: str
    api_base_url: str
    api_key: str | None
    session_secret: str
    session_cookie_secure: bool
    session_ttl_seconds: int
    provider_timeout_seconds: float
    frontend_dist_path: Path

    @classmethod
    def from_env(cls) -> Settings:
        """Read deployment configuration without exposing credentials."""
        load_dotenv()
        provider_name = os.getenv("IMAGE_PROVIDER", "openai").strip().lower()
        api_key = (
            os.getenv("OPENAI_API_KEY")
            if provider_name == "openai"
            else os.getenv("IMAGE_API_KEY")
        )
        base_url = (
            os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            if provider_name == "openai"
            else os.getenv("IMAGE_API_BASE_URL", "")
        )
        return cls(
            database_path=Path(os.getenv("IMAGE_DATABASE_PATH", "var/image-studio.db")),
            image_storage_path=Path(os.getenv("IMAGE_STORAGE_PATH", "var/images")),
            provider_name=provider_name,
            model_name=os.getenv("IMAGE_MODEL", "gpt-image-2.5-sunburst").strip(),
            api_base_url=base_url.rstrip("/"),
            api_key=api_key,
            session_secret=os.getenv(
                "SESSION_SECRET", "development-only-change-this-session-secret"
            ),
            session_cookie_secure=os.getenv("SESSION_COOKIE_SECURE", "false").lower()
            in {"1", "true", "yes"},
            session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "1209600")),
            provider_timeout_seconds=float(
                os.getenv("IMAGE_PROVIDER_TIMEOUT_SECONDS", "180")
            ),
            frontend_dist_path=Path(os.getenv("FRONTEND_DIST_PATH", "frontend/dist")),
        )

    def validate(self) -> None:
        if self.provider_name not in {"openai", "openai_compatible"}:
            raise ValueError("IMAGE_PROVIDER must be openai or openai_compatible.")
        if not self.model_name:
            raise ValueError("IMAGE_MODEL must not be empty.")
        if self.session_ttl_seconds < 60:
            raise ValueError("SESSION_TTL_SECONDS must be at least 60.")
        if self.provider_timeout_seconds <= 0:
            raise ValueError("IMAGE_PROVIDER_TIMEOUT_SECONDS must be positive.")


def make_settings(
    *,
    database_path: Path,
    image_storage_path: Path,
    frontend_dist_path: Path,
    **overrides: object,
) -> Settings:
    """Build explicit settings in tests and local development tools."""
    defaults: dict[str, object] = {
        "provider_name": "openai",
        "model_name": "gpt-image-2.5-sunburst",
        "api_base_url": "https://api.openai.com/v1",
        "api_key": None,
        "session_secret": "test-session-secret-that-is-long-enough",
        "session_cookie_secure": False,
        "session_ttl_seconds": 3600,
        "provider_timeout_seconds": 5.0,
    }
    defaults.update(overrides)
    return Settings(
        database_path=database_path,
        image_storage_path=image_storage_path,
        frontend_dist_path=frontend_dist_path,
        **defaults,  # type: ignore[arg-type]
    )
