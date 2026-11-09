"""Start the host ngrok agent from ignored local configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def _file_value(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def build_command(
    root: Path = ROOT, environ: Mapping[str, str] | None = None
) -> tuple[list[str], dict[str, str]]:
    """Build ngrok invocation without logging credentials."""
    environment = dict(os.environ if environ is None else environ)
    values = dotenv_values(root / ".env")

    def configured(name: str, fallback: str = "") -> str:
        return environment.get(name) or values.get(name) or fallback

    credential = _file_value(root / ".secrets/ngrok-basic-auth")
    if not credential or ":" not in credential:
        raise ValueError("ngrok Basic Auth file is missing or invalid.")

    token = configured(
        "NGROK_AUTHTOKEN", _file_value(root / ".secrets/ngrok-authtoken")
    )
    if token:
        environment["NGROK_AUTHTOKEN"] = token
    url = configured("NGROK_URL", _file_value(root / ".secrets/ngrok-url"))
    if url:
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("NGROK_URL must be an HTTPS endpoint URL without a path.")

    command = [
        "ngrok",
        "http",
        "8000",
        "--basic-auth",
        credential,
        "--log",
        "stdout",
        "--log-format",
        "json",
    ]
    if url:
        command.extend(["--url", url])
    return command, environment


def main() -> None:
    try:
        command, environment = build_command()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    os.execvpe("ngrok", command, environment)


if __name__ == "__main__":
    main()
