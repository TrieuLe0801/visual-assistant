# Project Status

Last updated: 2026-11-14

## Current milestone

MVP implemented. Users can select 1–6 images per creation action and delete
images from their library. Earlier offline tests and the current frontend build
pass; the latest pytest run has one failure documented below. The
updated backend/frontend are running in the existing Compose stack; local and
public health checks returned HTTP 200. The named Cloudflare Tunnel serves
`aliter.app`; its public `/api/health` returned HTTP 200 on 2026-11-14.
Registration is disabled in the UI and
API; existing accounts remain available. Live image generation still needs a
browser retry.

Security audit fixes are implemented and verified offline in this worktree:
explicit session secret, Secure cookie default, API no-store headers, persistent
safety rate limits, bounded provider responses and Pillow 13 in the Python 3.11
Trixie deployment image. Docker Scout found 27 residual runtime advisories,
none high or critical. These security changes are now deployed to the local
Compose stack. Registration remains disabled by default. See
[audit report](docs/security-audit-2026-11-10.md) and
[ADR 0010](docs/adr/0010-security-guards.md).

Python support is now `>=3.11`; the active lockfile requires Pillow 13.0.0+.
Python 3.10 is rejected before dependency installation. See
[ADR 0011](docs/adr/0011-drop-python-310-for-pillow-security.md).

Active plan: [docs/implementation-plan.md](docs/implementation-plan.md).
Active charter: [docs/project-charter.md](docs/project-charter.md).
Current log: [docs/learning-log/2026-11-08-image-studio.md](docs/learning-log/2026-11-08-image-studio.md).

Current worktree verification on 2026-11-14: `uv run pytest` reports 39 passed
and 1 failed. The deployment-settings test expects the default Secure cookie,
but the ignored local `.env` sets `SESSION_COOKIE_SECURE=false` for HTTP
development. The test and runtime settings were not changed to hide the failure.
Frontend build and Python style checks pass; see the current log.

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
- Added server-side Vietnamese prompt interpretation for generation, editing and
  variations; the library retains the user's original text. See
  [ADR 0008](docs/adr/0008-vietnamese-prompt-interpretation.md).
- Added a 1–6 image selector that makes separate requests, plus owner-scoped
  deletion of image files and library entries. Derived image records keep their
  source relationship; see [ADR 0009](docs/adr/0009-image-batch-and-deletion.md).
- Built an arm64 Docker image and healthy single-host Compose container with a
  persistent SQLite/image volume and file-backed session secret. A stopped-app
  backup restored successfully into a separate verification volume; see
  [deployment guide](docs/deployment-compose-cloudflare.md) and [ADR 0007](docs/adr/0007-single-host-compose-cloudflare.md).
- Split Compose into a one-shot SQLite schema initializer, FastAPI backend,
  Nginx frontend and named Cloudflare Tunnel service. The tunnel uses a
  file-backed connector token and serves `aliter.app`.
- Audited source and dependencies; patched confirmed session, abuse, response
  buffering, cache and account-timing risks. Raised the minimum Python version
  to 3.11 so no supported environment resolves vulnerable Pillow 12.3.0.

## Implementation status

| Bước | Trạng thái | Bằng chứng |
|---|---|---|
| 1. Tài khoản, quyền sở hữu và lưu trữ bền vững | Hoàn thành | Auth, owner-isolation, file access và restart tests |
| 2. Generation, edit, variation và provider errors | Hoàn thành offline | Fake-provider, adapter, unsupported capability, invalid/oversized image và storage-failure tests |
| 2a. LangChain model routing và LangSmith tracing | Hoàn thành offline | 6 model-routing/trace tests; chưa xác nhận LangSmith remote |
| 2b. Hiểu prompt tiếng Việt | Offline verified; live model còn chờ | 2 HTTP mock/API tests qua; latest source image đã deploy nhưng chưa kiểm tra live prompt |
| 3. Giao diện và production build | Hoàn thành offline | SPA/static tests; TypeScript + Vite build passed |
| 4. Live OpenAI/self-hosted smoke tests | Đang chờ retry generation | Lần gần nhất 502 do container chưa nhận key; backend đã recreate; GET `/models` 200, model cấu hình có trong danh sách |
| 5. Docker Compose local deployment | Hoàn thành | backend/frontend images, database init exit 0, both long-running services healthy, HTTP proxy, backup/restore |
| 6. Cloudflare public tunnel | Named tunnel đang chạy trên `aliter.app` | Running `cloudflared` uses a token file; public `/api/health` returned HTTP 200 on 2026-11-14; Access policy not verified |
| 7. Chọn 1–6 ảnh và xóa ảnh | Đã deploy; live generation còn chờ | Offline API tests, frontend build, Compose health và public health qua |
| 8. Security audit và vá lỗi | Đã deploy local Compose | 40 tests trên Python 3.11 trước triển khai; dependency audit sạch; Python 3.10 bị từ chối; Docker Scout còn 27 cảnh báo mức trung bình/thấp; local/public health 200 |

## Now

1. Retry image generation in the browser, including a multi-image action.
   Verify prompt interpretation and output separately from health checks.
2. Retry image generation in the browser after the security-patched image
   rollout; confirm Vietnamese prompt interpretation and output.
3. Confirm the intended Cloudflare Access policy for `aliter.app` before
   sharing the domain more widely.
4. Verify `PROMPT_MODEL` against the configured API, then run separate OpenAI
   and self-hosted operation checks.
5. Schedule off-host copies of the documented stopped-app backup before
   storing production data.

## Next

- Record live provider results and any provider-specific capability gaps.
- Consider asynchronous jobs or object storage only if real deployment needs
  require them.

Registration is temporarily closed. To reopen, set `REGISTRATION_ENABLED=true`
in the ignored `.env` file and recreate the app container.

## Dependencies and limits

The default provider/model are admin configuration; the UI does not expose
them. `IMAGE_MODEL_CATALOG` and `IMAGE_ACTIVE_MODEL` select a server-side model
at startup. LangSmith tracing is opt-in and excludes prompt/image content.
Live provider behavior and remote trace delivery remain unverified. SQLite and local files target a
single application host; a manual backup/restore path exists, but scheduled
off-host backup and multi-host coordination are not included.
Each prompt is also sent to the configured language model for interpretation;
this adds a model request, latency and cost before the image-provider request.
Provider calls run synchronously, so a request can remain open while an image
is generated.

## Verification

- Named tunnel documentation cleanup (2026-11-14): the running Compose
  `cloudflared` command uses `run --token-file`, and
  `https://aliter.app/api/health` returned HTTP 200. Public and local frontend
  HTML had the same SHA-256. Both Compose config variants, JSON parsing,
  isort, Black, flake8, Ruff, frontend build, lock check and diff check passed.
  `uv run pytest` still reports 39 passed, 1 failed in the previously recorded
  local `.env` Secure-cookie test; no test or application code was changed.
- Codex workflow review (2026-11-14): four agent TOMLs and the remaining
  deployment skill validated. `uv run pytest` reported 39 passed, 1 failed
  (`test_session_secret_file_overrides_environment`); isort, Black, flake8,
  Ruff, frontend build and `git diff --check` passed. This is current worktree
  evidence, separate from the historical results below.
- Current project Python: CPython 3.11.16 via uv; Pillow 13.0.0. System
  `python3` is 3.9.6. The earlier Python 3.10.21 checks below are historical.
- Python 3.10/Pillow follow-up: `uv run pytest -q` 40 passed on Python 3.11;
  isort, Black, flake8, Ruff, Bandit, lock check, frontend build and isolated
  Docker build passed. `pip-audit` found no known vulnerabilities in the locked
  production dependencies. Explicit Python 3.10 selection failed before
  installation, as required. The running Compose stack was not updated.
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
- Vietnamese prompt interpreter change (2026-11-09): 2 focused HTTP mock/API
  tests passed; full pytest suite 29 passed. isort, Black, flake8, Ruff,
  frontend TypeScript/Vite build, Compose config and diff check passed. Live
  prompt and image calls remain unverified.
- `docker compose config --quiet`, `docker compose --profile publish config --quiet`,
  `docker compose build app frontend` and `docker compose up -d --wait`: passed.
- Database initializer exited 0. Backend and frontend healthy. Local
  `/api/health`, frontend root and SPA route: HTTP 200; unauthenticated
  `/api/images`: HTTP 401. Backend has no host port.
- Compose secret and Secure cookie configuration confirmed inside backend.
  Internal Compose-network request to `frontend:80/api/health`: HTTP 200.
- Stopped-app volume backup restored into a separate volume; SQLite integrity
  check: `ok`; image directory present.
- Historical temporary tunnel check (2026-11-09): the connector registered
  over QUIC and public `/api/health` returned HTTP 200. The named tunnel
  replaced that route.
- User's image-generation attempt returned HTTP 502. Cloudflare health stayed
  HTTP 200. At failure time, `.env` had an OpenAI key but the backend container
  had no `OPENAI_API_KEY`; the failed operation recorded a credentials error.
- Recreated only the backend with
  `docker compose up -d --no-deps --force-recreate app`. It is healthy and now
  has the key. Read-only OpenAI `GET /models`: HTTP 200; configured image model
  listed. No image-generation request was retried.
- Live image generation, prompt interpretation, LangSmith remote delivery and
  browser-driven E2E remain unverified.
- Delete/count deployment (2026-11-09): focused `uv run pytest
  tests/test_database.py tests/test_image_studio.py -q` passed (20 tests);
  full `uv run pytest` passed (32 tests); isort, Black, flake8, Ruff and
  `git diff --check` passed;
  frontend `npm run build` passed. New backend and frontend images built and
  healthy in the existing `visual-assistant` Compose project. Stopped-app
  backup passed `gzip -t`; SQLite `PRAGMA integrity_check` returned `ok`, and
  the new `deleted_at` column exists. Local `/api/health` and frontend returned
  HTTP 200; unauthenticated DELETE returned 401. The prior public tunnel
  `/api/health` returned HTTP 200. Live image creation and browser UI behavior
  were not tested.
