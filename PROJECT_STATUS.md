# Project Status

Last updated: 2026-11-08

## Current milestone

MVP implemented and offline verified. Live OpenAI and self-hosted provider
checks remain pending because no real credentials or endpoint were supplied for
this verification.

Active plan: [docs/implementation-plan.md](docs/implementation-plan.md).
Active charter: [docs/project-charter.md](docs/project-charter.md).
Current log: [docs/learning-log/2026-11-08-image-studio.md](docs/learning-log/2026-11-08-image-studio.md).

The image-studio scope replaces the travel-planner product. The previous
charter and implementation plan are preserved under
[`docs/archive/2026-10-14/`](docs/archive/2026-10-14/README.md). No travel
planner completion counts carry forward.

## Done

- Recorded image-studio requirements, provider/storage decisions, MVP limits
  and acceptance scenarios in the charter and [ADR 0005](docs/adr/0005-ai-image-studio.md).
- Implemented FastAPI email/password auth, signed sessions, SQLite records,
  owner-scoped image access and local-volume storage.
- Added provider interface and OpenAI/OpenAI-compatible adapters for image
  generation, editing and variations.
- Added prompt/status/metadata persistence, source relationships, image
  validation, 20 MiB output limit and safe provider/storage failures.
- Built React/TypeScript screens for auth, library, prompt creation, image
  details, edit, variation and download.
- Added offline tests with fake provider and HTTP transport. Full suite passes.
- Added frontend lockfile and recorded the active environment baseline.
- Split backend into AI services, SQLite settings/connection/repository modules,
  and reusable security/image/time utilities without changing API routes.
- Added server-selected LangChain Core model routing and metadata-only LangSmith
  operation traces; see [ADR 0006](docs/adr/0006-langchain-model-routing-langsmith-tracing.md).
- Built an arm64 Docker image and healthy single-host Compose container with a
  persistent SQLite/image volume and file-backed session secret. A stopped-app
  backup restored successfully into a separate verification volume; see
  [deployment guide](docs/deployment-compose-ngrok.md) and [ADR 0007](docs/adr/0007-single-host-compose-ngrok.md).
- Split Compose into a one-shot SQLite schema initializer, FastAPI backend,
  Nginx frontend and optional ngrok publish service. Backend and frontend are
  healthy; ngrok configuration validates without opening a public tunnel.

## Implementation status

| Bước | Trạng thái | Bằng chứng |
|---|---|---|
| 1. Tài khoản, quyền sở hữu và lưu trữ bền vững | Hoàn thành | Auth, owner-isolation, file access và restart tests |
| 2. Generation, edit, variation và provider errors | Hoàn thành offline | Fake-provider, adapter, unsupported capability, invalid/oversized image và storage-failure tests |
| 2a. LangChain model routing và LangSmith tracing | Hoàn thành offline | 6 model-routing/trace tests; chưa xác nhận LangSmith remote |
| 3. Giao diện và production build | Hoàn thành offline | SPA/static tests; TypeScript + Vite build passed |
| 4. Live OpenAI/self-hosted smoke tests | Chưa chạy | Cần endpoint và credentials; không có model call trong lần kiểm chứng này |
| 5. Docker Compose local deployment | Hoàn thành | backend/frontend images, database init exit 0, both long-running services healthy, HTTP proxy, backup/restore |
| 6. Ngrok public tunnel | Compose sẵn sàng; chưa publish | Ngrok container/secret/profile config kiểm tra; chờ `NGROK_AUTHTOKEN` và domain khả dụng |

## Now

1. Supply an available ngrok account/domain configuration, then verify the
   public HTTPS endpoint with Basic Auth.
2. When provider credentials and endpoint are available, run separate OpenAI and
   self-hosted generation/edit/variation smoke checks.
3. Schedule off-host copies of the documented stopped-app backup before
   storing production data.

## Next

- Record live provider results and any provider-specific capability gaps.
- Consider asynchronous jobs or object storage only if real deployment needs
  require them.

## Dependencies and limits

The default provider/model are admin configuration; the UI does not expose
them. `IMAGE_MODEL_CATALOG` and `IMAGE_ACTIVE_MODEL` select a server-side model
at startup. LangSmith tracing is opt-in and excludes prompt/image content.
Live provider behavior and remote trace delivery remain unverified. SQLite and local files target a
single application host; a manual backup/restore path exists, but scheduled
off-host backup and multi-host coordination are not included.
Provider calls run synchronously, so a request can remain open while an image
is generated.

## Verification

- Project Python: CPython 3.10.21 via uv; system `python3` is 3.9.6.
- `uv sync --locked`: passed; 58 packages checked.
- `uv lock --check`: passed; 66 packages resolved.
- `uv run pytest tests/test_image_studio.py`: 15 passed.
- `uv run pytest tests/test_model_routing.py`: 6 passed.
- `uv run pytest`: 30 passed (28 application/deployment tests and 2 development-hook tests).
- `uv run pytest tests/test_database.py tests/test_image_studio.py`: 17 passed.
- isort, Black, flake8 and Ruff standard checks: passed.
- `npm ci --offline`: passed; no vulnerabilities reported.
- `npm run build`: passed with Vite 8.3.6.
- `git diff --check`: passed.
- `docker compose config --quiet`, `docker compose --profile publish config --quiet`,
  `docker compose build app frontend` and `docker compose up -d --wait`: passed.
- Database initializer exited 0. Backend and frontend healthy. Local
  `/api/health`, frontend root and SPA route: HTTP 200; unauthenticated
  `/api/images`: HTTP 401. Backend has no host port.
- Compose secret and Secure cookie configuration confirmed inside backend.
  Internal Compose-network request to `frontend:80/api/health`: HTTP 200.
- Stopped-app volume backup restored into a separate volume; SQLite integrity
  check: `ok`; image directory present.
- Ngrok Compose service, Basic Auth secret mount and shell syntax validated.
  Tunnel not started; `NGROK_AUTHTOKEN` and `NGROK_URL` remain unset in `.env`.
  Previous host CLI attempt hit `ERR_NGROK_334` on an occupied domain.
- Live provider, LangSmith remote delivery, public HTTPS and browser-driven E2E checks: not run.
