# Image Studio — Environment baseline

Captured: 2026-11-08
Status: Initial toolchain inventory; project Python runtime verified.

## Product runtime

- Required Python: `>=3.10`.
- Project Python via `uv run`: CPython `3.10.21`.
- Python package/environment manager: `uv 0.12.19`.
- System `python3`: `3.9.6`; it does not meet the project requirement. App commands
  use the uv-managed interpreter.
- Node.js: `v24.13.0`.
- npm: `11.6.2`.
- Runtime image provider, credentials and self-hosted endpoint: not verified.
- SQLite and local-volume paths are created by the app. Backup/restore is not
  configured by this repository.

The first `uv python find 3.10` attempt was denied before reporting an
interpreter. This later command verified the project interpreter as CPython
`3.10.21`:

```bash
uv run --locked --cache-dir /private/tmp/visual-assistant-uv-cache python --version
```

## Frontend

Node and npm versions were recorded with `node --version` and `npm --version`.
Dependency versions are locked in `frontend/package-lock.json`.
Production browser traffic uses the same-origin FastAPI build; the Vite dev
server proxies `/api` to the backend.

## Verification limits

No live OpenAI or self-hosted provider call is part of this environment capture.
Offline tests use a fake provider. Docker is not required for local execution.
