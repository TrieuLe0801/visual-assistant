"""Deployment-only secret file configuration."""

from pathlib import Path

import pytest

from image_studio.config import Settings


def test_session_secret_file_overrides_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "session-secret"
    path.write_text("file-secret-long-enough-for-test\n", encoding="utf-8")
    monkeypatch.setenv("SESSION_SECRET", "environment-secret-long-enough")
    monkeypatch.setenv("SESSION_SECRET_FILE", str(path))
    monkeypatch.delenv("SESSION_COOKIE_SECURE", raising=False)

    settings = Settings.from_env()

    assert settings.session_secret == "file-secret-long-enough-for-test"
    assert settings.session_cookie_secure is True
    assert "file-secret-long-enough-for-test" not in repr(settings)


def test_missing_session_secret_file_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SESSION_SECRET_FILE", str(tmp_path / "missing"))

    with pytest.raises(ValueError, match="SESSION_SECRET_FILE"):
        Settings.from_env()


def test_missing_or_sample_session_secret_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SESSION_SECRET_FILE", raising=False)
    for value in ("", "development-only-change-this-session-secret"):
        monkeypatch.setenv("SESSION_SECRET", value)
        with pytest.raises(ValueError, match="SESSION_SECRET"):
            Settings.from_env()


def test_sample_secret_file_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "sample-secret"
    path.write_text("development-only-change-this-session-secret\n", encoding="utf-8")
    monkeypatch.setenv("SESSION_SECRET_FILE", str(path))
    with pytest.raises(ValueError, match="SESSION_SECRET"):
        Settings.from_env()
