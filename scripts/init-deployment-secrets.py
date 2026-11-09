"""Create ignored local secrets for the Compose and ngrok deployment."""

import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET_DIR = ROOT / ".secrets"


def create_if_missing(name: str, value: str) -> None:
    path = SECRET_DIR / name
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(value + "\n")


def main() -> None:
    SECRET_DIR.mkdir(mode=0o700, exist_ok=True)
    create_if_missing("session_secret", secrets.token_urlsafe(48))
    create_if_missing("ngrok-basic-auth", "studio:" + secrets.token_urlsafe(24))
    print("Deployment secret files are ready in .secrets/.")


if __name__ == "__main__":
    main()
