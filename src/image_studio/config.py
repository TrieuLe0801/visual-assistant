"""Runtime settings loaded from environment variables."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from .database.settings import DatabaseSettings


@dataclass(frozen=True)
class ImageModelProfile:
    alias: str
    provider_name: str
    model_name: str
    api_base_url: str
    api_key: str | None = field(repr=False)


@dataclass(frozen=True)
class PromptModelSettings:
    model_name: str = "gpt-6-luna"
    api_base_url: str = "https://api.openai.com/v1"
    api_key: str | None = field(default=None, repr=False)
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class Settings:
    database: DatabaseSettings
    image_storage_path: Path
    provider_name: str
    model_name: str
    api_base_url: str
    api_key: str | None = field(repr=False)
    session_secret: str = field(repr=False)
    session_cookie_secure: bool
    session_ttl_seconds: int
    provider_timeout_seconds: float
    frontend_dist_path: Path
    prompt_model: PromptModelSettings = field(default_factory=PromptModelSettings)
    model_catalog: tuple[ImageModelProfile, ...] = ()
    active_model: str = "default"

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
        openai_base_url = os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        ).rstrip("/")
        prompt_base_url = os.getenv("PROMPT_API_BASE_URL", openai_base_url).rstrip("/")
        prompt_api_key = os.getenv("PROMPT_API_KEY")
        if not prompt_api_key and prompt_base_url == openai_base_url:
            prompt_api_key = os.getenv("OPENAI_API_KEY")
        model_catalog = _model_catalog_from_env(os.getenv("IMAGE_MODEL_CATALOG", ""))
        return cls(
            database=DatabaseSettings.from_env(),
            image_storage_path=Path(os.getenv("IMAGE_STORAGE_PATH", "var/images")),
            provider_name=provider_name,
            model_name=os.getenv("IMAGE_MODEL", "gpt-image-2.5-sunburst").strip(),
            api_base_url=base_url.rstrip("/"),
            api_key=api_key,
            session_secret=_session_secret_from_env(),
            session_cookie_secure=os.getenv("SESSION_COOKIE_SECURE", "false").lower()
            in {"1", "true", "yes"},
            session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "1209600")),
            provider_timeout_seconds=float(
                os.getenv("IMAGE_PROVIDER_TIMEOUT_SECONDS", "180")
            ),
            frontend_dist_path=Path(os.getenv("FRONTEND_DIST_PATH", "frontend/dist")),
            prompt_model=PromptModelSettings(
                model_name=os.getenv("PROMPT_MODEL", "gpt-6-luna").strip(),
                api_base_url=prompt_base_url,
                api_key=prompt_api_key,
                timeout_seconds=float(os.getenv("PROMPT_TIMEOUT_SECONDS", "30")),
            ),
            model_catalog=model_catalog,
            active_model=os.getenv("IMAGE_ACTIVE_MODEL", "default").strip(),
        )

    def validate(self) -> None:
        if not self.model_catalog:
            if self.provider_name not in {"openai", "openai_compatible"}:
                raise ValueError("IMAGE_PROVIDER must be openai or openai_compatible.")
            if not self.model_name:
                raise ValueError("IMAGE_MODEL must not be empty.")
        if self.session_ttl_seconds < 60:
            raise ValueError("SESSION_TTL_SECONDS must be at least 60.")
        if self.provider_timeout_seconds <= 0:
            raise ValueError("IMAGE_PROVIDER_TIMEOUT_SECONDS must be positive.")
        if not self.prompt_model.model_name:
            raise ValueError("PROMPT_MODEL must not be empty.")
        if self.prompt_model.timeout_seconds <= 0:
            raise ValueError("PROMPT_TIMEOUT_SECONDS must be positive.")
        aliases = [profile.alias for profile in self.model_catalog]
        if len(aliases) != len(set(aliases)):
            raise ValueError("IMAGE_MODEL_CATALOG aliases must be unique.")
        if self.active_model not in (aliases or ["default"]):
            raise ValueError("IMAGE_ACTIVE_MODEL must name a configured model.")
        for profile in self.model_catalog:
            if not profile.alias or not profile.model_name:
                raise ValueError(
                    "IMAGE_MODEL_CATALOG aliases and models must not be empty."
                )
            if profile.provider_name not in {"openai", "openai_compatible"}:
                raise ValueError("IMAGE_MODEL_CATALOG provider is unsupported.")


def _model_catalog_from_env(raw: str) -> tuple[ImageModelProfile, ...]:
    if not raw.strip():
        return ()
    try:
        catalog = json.loads(raw)
    except ValueError as exc:
        raise ValueError("IMAGE_MODEL_CATALOG must be valid JSON.") from exc
    if not isinstance(catalog, dict) or not catalog:
        raise ValueError("IMAGE_MODEL_CATALOG must be a nonempty object.")
    profiles = []
    for alias, entry in catalog.items():
        if not isinstance(alias, str) or not isinstance(entry, dict):
            raise TypeError("IMAGE_MODEL_CATALOG has an invalid entry.")
        if set(entry) != {"provider", "model"}:
            raise ValueError("IMAGE_MODEL_CATALOG entries need provider and model.")
        provider_name = entry["provider"]
        model_name = entry["model"]
        if not isinstance(provider_name, str) or not isinstance(model_name, str):
            raise TypeError("IMAGE_MODEL_CATALOG has an invalid entry.")
        if provider_name == "openai":
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider_name == "openai_compatible":
            base_url = os.getenv("IMAGE_API_BASE_URL", "")
            api_key = os.getenv("IMAGE_API_KEY")
        else:
            raise ValueError("IMAGE_MODEL_CATALOG provider is unsupported.")
        profiles.append(
            ImageModelProfile(
                alias=alias.strip(),
                provider_name=provider_name,
                model_name=model_name.strip(),
                api_base_url=base_url.rstrip("/"),
                api_key=api_key,
            )
        )
    return tuple(profiles)


def _session_secret_from_env() -> str:
    path = os.getenv("SESSION_SECRET_FILE")
    if path:
        try:
            return Path(path).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ValueError("SESSION_SECRET_FILE could not be read.") from exc
    return os.getenv("SESSION_SECRET", "development-only-change-this-session-secret")


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
        "model_catalog": (),
        "active_model": "default",
    }
    defaults.update(overrides)
    return Settings(
        database=DatabaseSettings(path=database_path),
        image_storage_path=image_storage_path,
        frontend_dist_path=frontend_dist_path,
        **defaults,  # type: ignore[arg-type]
    )
