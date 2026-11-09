"""Ignored ngrok configuration loads without shell-evaluating .env."""

from pathlib import Path

import pytest

from scripts.ngrok_publish import build_command


def _basic_auth_file(root: Path) -> None:
    directory = root / ".secrets"
    directory.mkdir()
    (directory / "ngrok-basic-auth").write_text(
        "studio:local-password\n", encoding="utf-8"
    )


def test_ngrok_reads_token_and_url_from_dotenv(tmp_path: Path) -> None:
    _basic_auth_file(tmp_path)
    (tmp_path / ".env").write_text(
        'NGROK_AUTHTOKEN="env-token"\n'
        'NGROK_URL="https://available.ngrok-free.dev"\n',
        encoding="utf-8",
    )
    (tmp_path / ".secrets/ngrok-authtoken").write_text("old-token\n", encoding="utf-8")

    command, environment = build_command(tmp_path, environ={})

    assert environment["NGROK_AUTHTOKEN"] == "env-token"
    assert command[-2:] == ["--url", "https://available.ngrok-free.dev"]
    assert "env-token" not in command
    assert command[command.index("--basic-auth") + 1] == "studio:local-password"


def test_ngrok_rejects_url_with_path(tmp_path: Path) -> None:
    _basic_auth_file(tmp_path)
    (tmp_path / ".env").write_text(
        "NGROK_URL=https://available.ngrok-free.dev/private\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="NGROK_URL"):
        build_command(tmp_path, environ={})


def test_ngrok_uses_fallback_file_when_dotenv_has_no_token(tmp_path: Path) -> None:
    _basic_auth_file(tmp_path)
    (tmp_path / ".env").write_text("NGROK_AUTHTOKEN=\n", encoding="utf-8")
    (tmp_path / ".secrets/ngrok-authtoken").write_text(
        "fallback-token\n", encoding="utf-8"
    )

    command, environment = build_command(tmp_path, environ={})

    assert environment["NGROK_AUTHTOKEN"] == "fallback-token"
    assert "--url" not in command
